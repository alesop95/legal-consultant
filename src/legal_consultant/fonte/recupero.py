"""Recupero di atti da Normattiva nella collezione supplementare locale.

Mette insieme il client dell'API (`normattiva`) e il convertitore (`akn`) e scrive i
file Markdown dove l'indicizzatore li trova. È il pezzo condiviso fra il recupero
massivo delle classi mancanti (`scripts/fetch_normattiva.py`) e il recupero di un
singolo atto per URN (`scripts/fetch_atto.py`), così che esista un solo percorso di
scrittura e non due da tenere allineati.

Il vincolo che determina la collocazione dei file: `data/italia-corpus` è un clone di un
repository terzo e viene riallineato con `fetch` più `reset --hard` a ogni
aggiornamento, quindi qualunque file scritto lì verrebbe distrutto senza preavviso. Il
materiale che non viene da lì vive in una radice separata, esattamente come già fa
`data/codici-extra`, e l'indicizzatore considera tutte le radici.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from ..config import long_path
from . import akn
from .normattiva import Client, AttoRef

# Denominazione dell'API -> cartella di collezione. Il primo segmento del percorso
# relativo alla radice diventa il campo `collezione` dell'indice (vedi
# `ingest/parser.py`), quindi questi nomi sono ciò che l'utente vede nelle citazioni.
COLLEZIONI = {
    "LEGGE": "Leggi",
    "DECRETO-LEGGE": "Decreti-legge",
    "COSTITUZIONE": "Costituzione",
    "LEGGE COSTITUZIONALE": "Leggi costituzionali",
    "DECRETO LEGISLATIVO": "Decreti legislativi",
    "DECRETO DEL PRESIDENTE DELLA REPUBBLICA": "DPR",
}

# Nome dei file dentro l'archivio: `LEGGE_20260608_101/2026-06-16_26G00118_VIGENZA_2026-07-29_V0.xml`.
_VIGENZA_RE = re.compile(r"VIGENZA_(\d{4}-\d{2}-\d{2})")


def collezione_per(denominazione: str) -> str:
    d = (denominazione or "").strip().upper()
    if d in COLLEZIONI:
        return COLLEZIONI[d]
    # Titolo leggibile per una tipologia non prevista, invece di inventare uno schema.
    return d.capitalize()


def _uno_per_atto(zf: zipfile.ZipFile) -> list[str]:
    """Un file XML per atto: l'archivio ha una cartella per atto, e quando contiene più
    versioni si tiene quella con la data di vigenza più recente."""
    per_cartella: dict[str, tuple[str, str]] = {}
    for nome in zf.namelist():
        if not nome.lower().endswith(".xml"):
            continue
        cartella = nome.rsplit("/", 1)[0]
        m = _VIGENZA_RE.search(nome)
        vigenza = m.group(1) if m else ""
        precedente = per_cartella.get(cartella)
        if precedente is None or vigenza > precedente[1]:
            per_cartella[cartella] = (nome, vigenza)
    return [nome for nome, _ in per_cartella.values()]


def scrivi_archivio(
    zip_bytes: bytes,
    radice: str | Path,
    denominazione: str,
    solo_urn: set[str] | None = None,
) -> tuple[list[str], list[str], int]:
    """Converte un archivio di export e scrive i Markdown sotto `radice/<collezione>`.

    Ritorna (percorsi relativi scritti, errori descritti, atti saltati).

    `solo_urn` è la lista bianca degli atti da scrivere, e non è un'ottimizzazione: è un
    requisito di correttezza. L'export per anno restituisce tutta la tipologia di quell'anno
    comprese le norme abrogate, mentre il frontmatter che questo modulo scrive dichiara
    `vigente: true`; senza lista bianca una legge abrogata entrerebbe nell'indice come
    vigente, che è un errore peggiore della sua assenza. Il chiamante costruisce la lista
    dalle sole classi non abrogate enumerate presso la fonte. Verificato che le URN
    dell'enumerazione e quelle degli XML coincidono esattamente.
    """
    radice = Path(radice)
    cartella = radice / collezione_per(denominazione)
    cartella.mkdir(parents=True, exist_ok=True)

    scritti: list[str] = []
    errori: list[str] = []
    saltati = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for nome in _uno_per_atto(zf):
            try:
                atto = akn.converti(zf.read(nome))
            except (ValueError, KeyError) as e:
                errori.append(f"{nome}: {e}")
                continue
            if solo_urn is not None and atto.urn not in solo_urn:
                saltati += 1
                continue
            dest = cartella / f"{atto.slug}.md"
            try:
                with open(long_path(dest), "w", encoding="utf-8", newline="\n") as f:
                    f.write(atto.markdown())
            except OSError as e:
                errori.append(f"{dest.name}: {e}")
                continue
            scritti.append(f"{cartella.name}/{dest.name}")
    return scritti, errori, saltati


# Quanti atti mancanti al massimo in un singolo export. Il costo di un export è dominato
# dall'attesa di elaborazione presso la fonte e non dal numero di atti, quindi conviene
# chiedere lotti grandi: un lotto per anno costerebbe la stessa attesa di un lotto per
# decennio. Il tetto però non è libero, ed è tarato su misure e non a intuito: un lotto da
# 400 atti si completa in pochi minuti, mentre uno da 1200 non è arrivato a compimento in
# mezz'ora di attesa. La fonte evidentemente non prepara archivi grandi in tempi utili, e
# insistere significherebbe solo occupare il proprio turno senza risultato.
LOTTO_MAX = 400


def lotti_per_intervallo(refs: list[AttoRef], massimo: int = LOTTO_MAX):
    """Divide gli atti mancanti in lotti contigui per data, come (dal, al, atti).

    Ogni lotto diventa un solo export con filtro sull'intervallo di emanazione. Gli atti
    sono ordinati per data e spezzati a `massimo`: l'intervallo di ciascun lotto va dalla
    data del primo alla data dell'ultimo, quindi i lotti non si sovrappongono e insieme
    coprono tutte le lacune.
    """
    ordinati = sorted((r for r in refs if r.data), key=lambda r: (r.data, r.numero))
    for i in range(0, len(ordinati), massimo):
        gruppo = ordinati[i : i + massimo]
        yield gruppo[0].data, gruppo[-1].data, gruppo


def recupera_intervallo(
    client: Client,
    denominazione: str,
    radice: str | Path,
    solo_urn: set[str] | None,
    classe: str | None = None,
    dal: str | None = None,
    al: str | None = None,
    su_avanzamento=None,
) -> tuple[list[str], list[str], int]:
    """Scarica ed espande un intervallo di date di una tipologia.

    Passare `classe` restringe l'export alla sola classe di provvedimento richiesta, così
    non si scaricano gli atti abrogati per poi scartarli: sugli anni più lontani sono la
    maggioranza del volume. Senza `dal` e `al` si chiede l'intera tipologia, che ha senso
    solo per un atto unico come la Costituzione.
    """
    zip_bytes = client.export_zip(
        denominazione, classe=classe, dal=dal, al=al, su_avanzamento=su_avanzamento
    )
    return scrivi_archivio(zip_bytes, radice, denominazione, solo_urn)


def stampa_avanzamento(elaborati: int, totali: int) -> None:
    """Riporta l'avanzamento di un export mentre la fonte lo prepara.

    Serve perché un export che non arriva a compimento non deve essere indistinguibile da un
    export lento: senza questa traccia, un'attesa di mezz'ora sembra un blocco del comando.
    Il valore convenzionale -1 segnala che il filtro della fonte sta rifiutando la rotta di
    interrogazione, che è transitorio e non un errore.
    """
    if elaborati < 0:
        print("      (la fonte rallenta le interrogazioni, attendo)", flush=True)
    elif totali:
        print(f"      preparazione presso la fonte: {elaborati}/{totali}", flush=True)


def scompone_urn(urn: str) -> tuple[str, int | None, int | None]:
    """(denominazione, anno, numero) da una URN NIR, per costruire il filtro di ricerca.

    La Costituzione non porta numero, quindi anno e numero possono essere None: in quel
    caso il filtro per sola denominazione individua comunque un atto unico.
    """
    pulita = (urn or "").strip()
    if not pulita.startswith("urn:nir:"):
        raise ValueError(f"URN non in forma NIR: {urn!r}")
    corpo = pulita[len("urn:nir:") :]
    parti = corpo.split(":")
    if len(parti) < 2:
        raise ValueError(f"URN incompleta: {urn!r}")
    tipo_urn = parti[1]
    coda = parti[-1]
    m = re.match(r"^(?P<data>\d{4}-\d{2}-\d{2})(?:;(?P<num>[0-9]+))?", coda)
    anno = int(m.group("data")[:4]) if m else None
    numero = int(m.group("num")) if (m and m.group("num")) else None
    return _denominazione_da_urn(tipo_urn), anno, numero


def _denominazione_da_urn(tipo_urn: str) -> str:
    """Denominazione dell'API dal segmento di tipo della URN.

    Si ricava invertendo la mappa usata in `normattiva._URN_TIPO`, senza duplicarla: le
    forme non previste si ricostruiscono meccanicamente sostituendo i punti con spazi.
    """
    from .normattiva import _URN_TIPO

    for denominazione, segmento in _URN_TIPO.items():
        if segmento == tipo_urn:
            return denominazione
    return tipo_urn.replace(".", " ").upper()


def recupera_urn(
    client: Client, urn: str, radice: str | Path
) -> tuple[list[str], list[str]]:
    """Scarica un singolo atto identificato dalla sua URN NIR.

    Usa lo stesso export asincroni del recupero massivo, con il filtro ristretto a
    numero e anno: un solo percorso di codice invece di due, al prezzo di qualche
    secondo di attesa in più rispetto a una GET diretta.
    """
    denominazione, anno, numero = scompone_urn(urn)
    zip_bytes = client.export_zip(
        denominazione, classe=None, anno=anno, numero=numero
    )
    scritti, errori, _ = scrivi_archivio(zip_bytes, radice, denominazione)

    # L'export filtra per numero e anno, non per URN: se l'anno di pubblicazione non
    # coincide con quello dell'atto la risposta può contenere omonimi. Si tiene solo
    # l'atto richiesto, verificando la URN sul file scritto.
    atteso = _slug_atteso(urn, denominazione)
    if atteso:
        pertinenti = [p for p in scritti if Path(p).stem == atteso]
        for p in scritti:
            if p not in pertinenti:
                (Path(radice) / p).unlink(missing_ok=True)
        if not pertinenti and scritti:
            errori.append(
                f"{urn}: l'export ha restituito {len(scritti)} atti, nessuno corrispondente"
            )
        return pertinenti, errori
    return scritti, errori


def _slug_atteso(urn: str, denominazione: str) -> str:
    _, _, numero = scompone_urn(urn)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", urn)
    if not m or numero is None:
        return ""
    tipo = re.sub(r"[^a-z0-9]+", "-", denominazione.lower()).strip("-")
    return f"{tipo}-{m.group(1)}-{numero}"


def urn_presenti(conn) -> set[str]:
    """URN già presenti nell'indice, per non riscaricare ciò che c'è.

    Una sola passata sulla tabella: su qualche milione di righe costa pochi secondi e
    permette di scrivere solo le lacune reali.
    """
    return {
        r[0]
        for r in conn.execute("SELECT DISTINCT urn FROM chunks WHERE urn <> ''")
    }


def refs_mancanti(refs: list[AttoRef], presenti: set[str]) -> list[AttoRef]:
    """Sottoinsieme degli atti attesi che l'indice non contiene."""
    return [r for r in refs if r.urn not in presenti]
