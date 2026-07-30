"""Client dell'API Open Data di Normattiva.

Normattiva pubblica da dicembre 2024 un'API Open Data documentata: la specifica
OpenAPI sta su `https://dati.normattiva.it/assets/come_fare_per/openapi-bff-opendata.json`
e il gateway è dichiarato in chiaro in `https://dati.normattiva.it/assets/env.js`.
Non dichiara schemi di sicurezza e risponde senza credenziali. Si usano tre capacità.

La prima è la tipologica delle denominazioni di atto, che è l'elenco canonico delle
trenta classi di atto normativo statale, e serve da denominatore per il controllo di
completezza: è l'unico modo di sapere che cosa dovrebbe esserci senza fidarsi
dell'elenco di ciò che c'è.

La seconda è la ricerca avanzata, che restituisce il conteggio autorevole degli atti
per tipologia e classe di provvedimento e li pagina fino a mille per volta: serve per
enumerare gli atti attesi e confrontarli uno per uno con l'indice locale.

La terza è l'export asincrono, che è il modo corretto di scaricare molti atti: una
richiesta produce un archivio ZIP di file Akoma Ntoso, uno per atto, consolidati alla
data di vigenza richiesta. La via alternativa, cioè l'export per singolo atto
`/do/atto/caricaAKN` del sito, richiede due richieste HTTP per atto con una sessione a
cookie condivisi, e per le circa undicimila lacune misurate avrebbe significato
ventiduemila richieste alla fonte invece di poche decine: qui si usa quindi l'export
asincrono anche per il recupero di un solo atto, così che il codice abbia un solo
percorso invece di due da mantenere.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

BASE = "https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1"

# User-Agent descrittivo e veritiero: identifica lo strumento invece di camuffarsi da
# browser. Verificato che l'API risponde regolarmente con questa identità.
USER_AGENT = "legge-it/1.0 (consulente legale locale, uso privato)"

# Classi di provvedimento della tipologica `/tipologiche/classe-provvedimento`.
CLASSE_SENZA_AGGIORNAMENTI = "1"
CLASSE_AGGIORNATO = "2"
CLASSE_ABROGATO = "3"
# Le due classi che compongono il diritto ancora in vigore.
CLASSI_VIGENTI = (CLASSE_SENZA_AGGIORNAMENTI, CLASSE_AGGIORNATO)

# Stati della ricerca asincrona (campo `stato` di StatusRicercaAsincronaDTO).
_STATO_ELABORATA = 3
_STATO_ERRORE = 4
_STATO_SOVRACCARICO = 5

_PER_PAGINA_MAX = 1000

# Cadenza del polling sullo stato di un export. Valori alti di proposito: vedi la nota in
# `Client._attendi`, dove è spiegato perché interrogare meno spesso è più veloce.
_ATTESA_INIZIALE = 25.0
_ATTESA_MASSIMA = 90.0

# Quanti 409 consecutivi sulla rotta di polling bastano a concludere che il filtro della
# fonte ha imposto un limite durevole a questo client, e non che l'export sia lento. Il
# comportamento è stato osservato: dopo un'attività di export sostenuta il WAF rifiuta
# quella sola rotta, mentre ricerca ed export continuano a rispondere, e non cede più nel
# giro di decine di minuti. Meglio dichiararlo e fermarsi che restare in attesa.
_MAX_409_CONSECUTIVI = 8


class NormattivaError(RuntimeError):
    """Errore non recuperabile nel dialogo con l'API di Normattiva."""


class NormattivaSovraccarico(NormattivaError):
    """La fonte ha rifiutato la richiesta per carico eccessivo (stato 5 o HTTP 503).

    Distinta dall'errore generico perché il chiamante può ritentare più tardi senza
    che nulla sia andato storto: non è un difetto della richiesta.
    """


@dataclass(frozen=True)
class AttoRef:
    """Riferimento a un atto come lo descrive la ricerca avanzata di Normattiva."""

    tipo: str
    numero: str
    anno: str
    data: str  # ISO, AAAA-MM-GG
    codice_redazionale: str
    titolo: str

    @property
    def urn(self) -> str:
        return f"urn:nir:stato:{_urn_tipo(self.tipo)}:{self.data};{self.numero}"


# Denominazione dell'API -> segmento di tipo nella URN NIR. Le URN del corpus usano il
# nome del tipo in minuscolo coi punti al posto degli spazi; qui si elencano solo le
# tipologie che questo modulo scarica, per non inventare forme non verificate.
_URN_TIPO = {
    "LEGGE": "legge",
    "LEGGE COSTITUZIONALE": "legge.costituzionale",
    "DECRETO-LEGGE": "decreto.legge",
    "DECRETO LEGISLATIVO": "decreto.legislativo",
    "COSTITUZIONE": "costituzione",
    "DECRETO DEL PRESIDENTE DELLA REPUBBLICA": "decreto.del.presidente.della.repubblica",
}


def _urn_tipo(denominazione: str) -> str:
    d = (denominazione or "").strip().upper()
    if d in _URN_TIPO:
        return _URN_TIPO[d]
    return d.lower().replace("-", ".").replace(" ", ".")


class Client:
    """Client HTTP dell'API Open Data, senza dipendenze esterne.

    Usa solo `urllib` della libreria standard, coerentemente col resto del progetto,
    che non ha dipendenze di rete. Ogni chiamata ritenta con attesa crescente sugli
    errori transitori, e tratta l'HTTP 409 del WAF come transitorio: il sistema di
    protezione dell'IPZS lo restituisce quando le richieste sono troppo ravvicinate,
    e cede se si rallenta. Verificato sul campo, non ipotizzato.
    """

    def __init__(self, pausa: float = 1.0, tentativi: int = 4, timeout: float = 120.0):
        self.pausa = pausa
        self.tentativi = tentativi
        self.timeout = timeout

    # -- trasporto -----------------------------------------------------------------

    def _richiesta(
        self,
        metodo: str,
        percorso: str,
        payload: dict | None = None,
        accetta: str = "application/json",
        url_assoluto: str | None = None,
        ritenta_409: bool = True,
    ) -> tuple[int, dict[str, str], bytes]:
        url = url_assoluto or (BASE + percorso)
        dati = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"User-Agent": USER_AGENT, "Accept": accetta}
        if dati is not None:
            headers["Content-Type"] = "application/json"

        ultimo: Exception | None = None
        for n in range(self.tentativi):
            req = urllib.request.Request(url, data=dati, headers=headers, method=metodo)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return r.status, dict(r.headers), r.read()
            except urllib.error.HTTPError as e:
                corpo = e.read()
                # 303 non è un errore: la ricerca asincrona lo usa per dire "pronto,
                # scarica da x-ipzs-location". urllib lo solleva perché non lo segue.
                if e.code == 303:
                    return e.code, dict(e.headers), corpo
                # Il 409 del WAF sulla rotta di polling non è un errore ma un "troppo
                # presto": chi interroga lo stato lo gestisce da sé rallentando, invece di
                # bruciare qui i tentativi con attese che si sommano.
                if e.code == 409 and not ritenta_409:
                    return e.code, dict(e.headers), corpo
                # 409 del WAF e 503/529 di sovraccarico: transitori, si rallenta.
                if e.code in (409, 503, 529) and n < self.tentativi - 1:
                    time.sleep(self.pausa * 4 * (n + 1))
                    ultimo = e
                    continue
                if e.code in (503, 529):
                    raise NormattivaSovraccarico(
                        f"{metodo} {url}: la fonte è sovraccarica (HTTP {e.code})"
                    ) from e
                raise NormattivaError(
                    f"{metodo} {url}: HTTP {e.code} {corpo[:200]!r}"
                ) from e
            except (urllib.error.URLError, OSError, TimeoutError) as e:
                ultimo = e
                if n < self.tentativi - 1:
                    time.sleep(self.pausa * 3 * (n + 1))
                    continue
                raise NormattivaError(f"{metodo} {url}: {e}") from e
        raise NormattivaError(f"{metodo} {url}: esauriti i tentativi ({ultimo})")

    def _json(self, metodo: str, percorso: str, payload: dict | None = None) -> dict:
        _, _, corpo = self._richiesta(metodo, percorso, payload)
        try:
            return json.loads(corpo.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as e:
            raise NormattivaError(f"{percorso}: risposta non JSON ({corpo[:120]!r})") from e

    # -- tipologiche ---------------------------------------------------------------

    def tipologie(self) -> list[str]:
        """Le denominazioni di atto che Normattiva stessa espone, in ordine di catalogo.

        È l'elenco canonico contro cui misurare la completezza: ricavarlo dalla fonte
        e non da una costante nel codice è il punto dell'esercizio, perché una costante
        cablata ripeterebbe esattamente l'errore che ha prodotto la lacuna del corpus.
        """
        d = self._json("GET", "/tipologiche/denominazione-atto")
        if not isinstance(d, list):
            raise NormattivaError("tipologica delle denominazioni: risposta inattesa")
        return [str(v.get("value", "")).strip() for v in d if v.get("value")]

    # -- ricerca avanzata ----------------------------------------------------------

    @staticmethod
    def _filtri(
        denominazione: str,
        classe: str | None,
        anno: int | None,
        dal: str | None = None,
        al: str | None = None,
    ) -> dict:
        f: dict[str, object] = {"denominazioneAtto": denominazione}
        if classe:
            f["classeProvvedimento"] = classe
        if anno:
            f["annoProvvedimento"] = anno
        # Intervallo sulla data di emanazione, cioè la stessa data che identifica l'atto
        # nella sua URN: permette di chiedere in un solo export un periodo di più anni.
        # Verificato coerente col filtro per anno singolo a parità di perimetro.
        if dal:
            f["dataInizioEmanazione"] = f"{dal}T00:00:00"
        if al:
            f["dataFineEmanazione"] = f"{al}T00:00:00"
        return f

    def conta(
        self, denominazione: str, classe: str | None = None, anno: int | None = None
    ) -> int:
        """Quanti atti la fonte dichiara per questa tipologia (e classe, e anno)."""
        payload = self._filtri(denominazione, classe, anno)
        payload["paginazione"] = {"paginaCorrente": 1, "numeroElementiPerPagina": 1}
        d = self._json("POST", "/ricerca/avanzata", payload)
        return int(d.get("numeroAttiTrovati") or 0)

    def enumera(
        self, denominazione: str, classe: str | None = None, anno: int | None = None
    ) -> list[AttoRef]:
        """Tutti gli atti di una tipologia (e classe, e anno), paginando fino in fondo."""
        out: list[AttoRef] = []
        pagina = 1
        atteso: int | None = None
        while True:
            payload = self._filtri(denominazione, classe, anno)
            payload["paginazione"] = {
                "paginaCorrente": pagina,
                "numeroElementiPerPagina": _PER_PAGINA_MAX,
            }
            d = self._json("POST", "/ricerca/avanzata", payload)
            if atteso is None:
                atteso = int(d.get("numeroAttiTrovati") or 0)
            lista = d.get("listaAtti") or []
            if not lista:
                break
            for a in lista:
                ref = _atto_ref(a)
                if ref is not None:
                    out.append(ref)
            if len(out) >= atteso or len(lista) < _PER_PAGINA_MAX:
                break
            pagina += 1
            time.sleep(self.pausa)
        return out

    # -- export asincrono ----------------------------------------------------------

    def export_zip(
        self,
        denominazione: str,
        classe: str | None = None,
        anno: int | None = None,
        numero: int | None = None,
        dal: str | None = None,
        al: str | None = None,
        formato: str = "AKN",
        vigenza: str = "V",
        attesa_max: float = 1800.0,
        su_avanzamento=None,
    ) -> bytes:
        """Archivio ZIP di file Akoma Ntoso per gli atti che soddisfano il filtro.

        Il flusso è quello documentato: `nuova-ricerca` restituisce 202 con un token,
        `conferma-ricerca` in PUT lo attiva, `check-status` si interroga fino al 303 che
        porta in `x-ipzs-location` l'URL di download. `vigenza` è 'V' per il testo
        vigente, 'O' per l'originario, 'M' per il multivigente. L'email non è richiesta e
        non viene inviata: nessun dato personale lascia la macchina.
        """
        filtri = self._filtri(denominazione, classe, anno, dal, al)
        if numero is not None:
            filtri["numeroProvvedimento"] = numero
        payload = {
            "formato": formato,
            "tipoRicerca": "A",
            "modalita": "C",
            "richiestaExport": vigenza,
            "parametriRicerca": filtri,
        }
        stato, _, corpo = self._richiesta("POST", "/ricerca-asincrona/nuova-ricerca", payload)
        token = corpo.decode("utf-8", errors="replace").strip().strip('"')
        if stato not in (200, 202) or not token:
            raise NormattivaError(
                f"nuova-ricerca: stato {stato}, token {token[:60]!r}"
            )

        conferma = self._json(
            "PUT", "/ricerca-asincrona/conferma-ricerca", {"token": token}
        )
        _verifica_stato(conferma)

        url_download = self._attendi(token, attesa_max, su_avanzamento)
        _, headers, zip_bytes = self._richiesta(
            "GET", "", accetta="*/*", url_assoluto=url_download
        )
        if not zip_bytes[:2] == b"PK":
            raise NormattivaError(
                f"download: il contenuto non è un archivio ZIP "
                f"(content-type {headers.get('Content-Type')!r})"
            )
        return zip_bytes

    def _attendi(self, token: str, attesa_max: float, su_avanzamento) -> str:
        """Interroga `check-status` fino al 303 e restituisce l'URL di download.

        Il polling è deliberatamente lento. Il WAF davanti al gateway risponde 409 a
        questa rotta quando le richieste sono ravvicinate, e lo fa in modo persistente:
        misurato, un polling ogni due secondi riceve 409 per oltre due minuti di fila
        senza mai vedere l'export, che era invece pronto. Interrogare meno spesso è quindi
        più veloce, non più lento, ed è anche il comportamento corretto verso la fonte. Per
        questo il primo controllo arriva dopo `_ATTESA_INIZIALE` secondi e il 409 viene
        trattato come "non ancora pronto" e non come errore.
        """
        scadenza = time.monotonic() + attesa_max
        intervallo = _ATTESA_INIZIALE
        consecutivi_409 = 0
        while time.monotonic() < scadenza:
            time.sleep(intervallo)
            intervallo = min(intervallo * 1.3, _ATTESA_MASSIMA)
            stato_http, headers, corpo = self._richiesta(
                "GET", f"/ricerca-asincrona/check-status/{token}", ritenta_409=False
            )
            if stato_http == 409:
                # Il WAF sta rifiutando la rotta: non è un errore, ma va reso visibile,
                # altrimenti un'attesa che non finisce mai è indistinguibile da un export
                # lento e il comando sembra bloccato senza dire perché.
                consecutivi_409 += 1
                if su_avanzamento is not None:
                    su_avanzamento(-1, -1)
                if consecutivi_409 >= _MAX_409_CONSECUTIVI:
                    raise NormattivaSovraccarico(
                        f"la fonte rifiuta l'interrogazione dello stato da "
                        f"{consecutivi_409} tentativi consecutivi: limite di traffico "
                        f"durevole, conviene riprovare più tardi"
                    )
                continue
            consecutivi_409 = 0
            if stato_http == 303:
                url = headers.get("x-ipzs-location") or headers.get("Location")
                if not url:
                    raise NormattivaError("check-status: 303 senza x-ipzs-location")
                return url
            try:
                d = json.loads(corpo.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            _verifica_stato(d)
            if su_avanzamento is not None:
                su_avanzamento(
                    int(d.get("attiElaborati") or 0), int(d.get("totAtti") or 0)
                )
        raise NormattivaError(
            f"check-status: export non pronto entro {attesa_max:.0f}s (token {token})"
        )


def _verifica_stato(d: dict) -> None:
    stato = d.get("stato")
    if stato == _STATO_ERRORE:
        raise NormattivaError(
            f"ricerca asincrona in errore: {d.get('descrizioneErrore') or d.get('descrizioneStato')}"
        )
    if stato == _STATO_SOVRACCARICO:
        raise NormattivaSovraccarico(
            f"ricerca asincrona rifiutata: {d.get('descrizioneStato')}"
        )


def _atto_ref(a: dict) -> AttoRef | None:
    """AttoRef da una riga di `listaAtti`, o None se i campi essenziali mancano."""
    numero = str(a.get("numeroProvvedimento") or "").strip()
    anno = str(a.get("annoProvvedimento") or "").strip()
    mese = str(a.get("meseProvvedimento") or "").strip()
    giorno = str(a.get("giornoProvvedimento") or "").strip()
    if not (numero and anno and mese and giorno):
        return None
    return AttoRef(
        tipo=str(a.get("denominazioneAtto") or "").strip(),
        numero=numero,
        anno=anno,
        data=f"{int(anno):04d}-{int(mese):02d}-{int(giorno):02d}",
        codice_redazionale=str(a.get("codiceRedazionale") or "").strip(),
        titolo=" ".join(str(a.get("titoloAtto") or "").split()),
    )
