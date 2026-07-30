"""Conversione dell'export Akoma Ntoso di Normattiva nel Markdown del corpus.

L'export della fonte è XML Akoma Ntoso, uno standard OASIS che marca esplicitamente
articoli, rubriche, commi e lettere invece di affidarli alla formattazione. Qui lo si
riduce allo stesso Markdown con frontmatter YAML che `ingest/parser.py` già sa leggere,
così che gli atti recuperati entrino nell'indice FTS5 dalla stessa porta di tutti gli
altri, senza un secondo percorso di ingestione da mantenere.

Due scelte di conversione vanno dichiarate perché non sono ovvie.

La prima riguarda la forma delle intestazioni di articolo. Il parser del progetto
riconosce la rubrica dopo un trattino oppure tra parentesi, e la collezione
supplementare già presente in `data/codici-extra` usa la forma con parentesi
(`### Art. 2. (Successione di leggi penali)`). Qui si emette la stessa forma, per non
introdurre una terza convenzione nel corpus.

La seconda riguarda le note. Normattiva annida in `authorialNote`, dentro il corpo
dell'articolo, il testo integrale delle norme richiamate: l'art. 1 della L. 219/2017 si
porterebbe dietro gli artt. 2, 13 e 32 della Costituzione. In un indice a granularità
di articolo quel testo è rumore che sposta il ranking verso l'articolo sbagliato, e
comparirebbe anche due volte perché la nota è annidata dentro il paragrafo che la
contiene. Le note vengono quindi escluse dal testo indicizzato. È una perdita
consapevole: il rinvio resta leggibile nel testo dell'articolo, il testo della norma
richiamata si trova cercando quella norma.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

_NS = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"

# Contenitori strutturali sopra l'articolo, dal più ampio al più stretto.
_CONTENITORI = ("book", "part", "title", "chapter", "section")

# Elementi che raggruppano contenuto senza essere essi stessi un blocco di testo.
_TRASPARENTI = ("list", "intro", "wrapUp", "content", "blockList", "toc")

# Elementi numerati dentro l'articolo: comma, lettera, numero, trattino.
_NUMERATI = ("paragraph", "point", "indent", "item", "subsection", "clause")

# Codice redazionale della Gazzetta: tre cifre più lettera più quattro cifre nei testi
# storici (078U0194), due cifre più lettera più cinque cifre nei recenti (26G00118).
_CODICE_RE = re.compile(r"^\d{2,3}[A-Z]\d{4,5}$")

# "Art. 11-bis." -> "11-bis"; "Articolo 5" -> "5"; "Art. unico" -> "unico".
_NUM_ART_RE = re.compile(r"^\s*Art(?:\.|icolo)?\s*(?P<num>[^\s].*?)\s*\.?\s*$", re.I)


@dataclass
class AttoAkn:
    """Un atto convertito: metadati per il frontmatter più il corpo in Markdown."""

    tipo: str
    numero: str
    data: str
    titolo: str
    urn: str
    codice_redazionale: str
    consolidato_al: str | None
    corpo: str
    n_articoli: int

    @property
    def slug(self) -> str:
        """Nome file stabile e breve, indipendente dal titolo.

        Il corpus principale nomina i file col titolo dell'atto, che produce percorsi
        lunghissimi e già costringe il progetto al prefisso extended-length su Windows.
        Qui si usa invece la terna tipo/data/numero, che identifica l'atto in modo
        univoco e resta corta.
        """
        tipo = re.sub(r"[^a-z0-9]+", "-", self.tipo.lower()).strip("-")
        parti = [p for p in (tipo, self.data, self.numero) if p]
        return "-".join(parti)

    def markdown(self) -> str:
        return _frontmatter(self) + "\n" + self.corpo.rstrip() + "\n"


def _locale(el: ET.Element) -> str:
    return el.tag.replace(_NS, "") if isinstance(el.tag, str) else ""


def _piatto(el: ET.Element) -> str:
    """Testo di un elemento, normalizzato, escludendo i sottoalberi delle note.

    Non si usa `itertext()` perché includerebbe il contenuto di `authorialNote`.
    """
    parti: list[str] = []

    def visita(e: ET.Element) -> None:
        if _locale(e) == "authorialNote":
            return
        if e.text:
            parti.append(e.text)
        for figlio in e:
            visita(figlio)
            if figlio.tail:
                parti.append(figlio.tail)

    visita(el)
    return " ".join("".join(parti).split())


def _testo_figlio(el: ET.Element, tag: str) -> str:
    figlio = el.find(_NS + tag)
    return _piatto(figlio) if figlio is not None else ""


def _righe(el: ET.Element, salta: ET.Element | None = None) -> list[str]:
    """Righe di testo di un elemento di corpo, in ordine di documento.

    I numeri di comma e di lettera vengono preservati come prefisso della riga: senza,
    il testo di un articolo diventa una sequenza di capoversi anonimi e la citazione
    puntuale di un comma non è più possibile. `salta` esclude un singolo sottoelemento
    già consumato altrove, tipicamente il paragrafo promosso a rubrica.
    """
    out: list[str] = []
    for figlio in el:
        tag = _locale(figlio)
        if tag in ("num", "heading", "authorialNote"):
            continue
        if salta is not None and figlio is salta:
            continue
        if tag in _NUMERATI:
            num = _testo_figlio(figlio, "num").strip()
            interne = _righe(figlio)
            if num and interne:
                interne[0] = f"{num} {interne[0]}".strip()
            elif num:
                interne = [num]
            out += interne
        elif tag in _TRASPARENTI:
            out += _righe(figlio)
        else:
            testo = _piatto(figlio)
            if testo:
                out.append(testo)
    return out


def _numero_articolo(num_grezzo: str, progressivo: int) -> str:
    """Numero dell'articolo da usare nell'intestazione, senza la parola "Art.".

    Il parser del progetto ricava il numero dall'intestazione: va quindi passato nudo.
    Se l'atto non lo dichiara si usa il progressivo, così che l'articolo resti citabile.
    """
    m = _NUM_ART_RE.match(num_grezzo or "")
    if m:
        num = m.group("num").strip().rstrip(".")
        # Le parentesi doppie di Normattiva marcano il testo modificato: fuori dal numero.
        num = num.strip("()").strip()
        if num:
            return num
    return str(progressivo)


# Lunghezza massima di un capoverso iniziale perché possa essere una rubrica e non già
# il primo comma dell'articolo. Sul campione di export misurato la mediana è 74
# caratteri; il valore anomalo osservato superava i settemila.
_RUBRICA_MAX = 250


def _rubrica(art: ET.Element) -> tuple[str, ET.Element | None]:
    """(rubrica dell'articolo, elemento da non ripetere nel corpo).

    Normalmente la rubrica sta in `heading`. Quando però Normattiva emette un `heading`
    vuoto, la rubrica compare come primo capoverso non numerato dell'articolo: senza
    riconoscerla, l'articolo entrerebbe nell'indice senza rubrica, e la rubrica è la
    colonna che pesa più di ogni altra nel ranking (peso 12 contro 1 del corpo), quindi
    la perdita si pagherebbe in recall su tutte le domande formulate col nomen iuris.

    L'euristica è ristretta a cinque condizioni congiunte: `heading` assente o vuoto,
    primo paragrafo figlio privo di `num`, testo più corto di `_RUBRICA_MAX`, presenza di
    altro contenuto dopo di esso nello stesso articolo, e testo che non termina con un
    punto. Le ultime due sono state aggiunte dopo un caso reale che le rendeva necessarie:
    negli articoli della Costituzione il testo dell'articolo È l'unico paragrafo non
    numerato, e senza quelle condizioni finiva promosso a rubrica lasciando il corpo
    dell'articolo vuoto, cioè un articolo indicizzato senza testo.

    Verificata su un anno intero di leggi: dei 295 articoli con `heading` pieno nessuno ha
    un primo paragrafo anonimo, quindi la promozione non può sottrarre il primo comma a un
    articolo che la rubrica ce l'ha già; e dei 42 candidati validi tutti hanno altro
    contenuto dopo di sé e nessuno termina con un punto, mentre nella Costituzione vale
    esattamente l'opposto in entrambi i casi.
    """
    esplicita = _testo_figlio(art, "heading").strip().strip("()").strip()
    if esplicita:
        return esplicita, None
    for figlio in art:
        if _locale(figlio) != "paragraph":
            continue
        if figlio.find(_NS + "num") is not None:
            return "", None
        testo = _piatto(figlio).strip()
        if not 0 < len(testo) <= _RUBRICA_MAX:
            return "", None
        if testo.rstrip().endswith("."):
            return "", None
        altro = any(
            c is not figlio
            and _locale(c) not in ("num", "heading", "authorialNote")
            and _piatto(c).strip()
            for c in art
        )
        if not altro:
            return "", None
        return testo.strip("()").strip(), figlio
    return "", None


def converti(xml_bytes: bytes) -> AttoAkn:
    """Converte un file Akoma Ntoso di Normattiva in un `AttoAkn`.

    Solleva ValueError se il documento non è un Akoma Ntoso riconoscibile o se manca la
    URN, che è l'unico identificatore su cui si regge tutto il resto della pipeline.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ValueError(f"XML non valido: {e}") from e
    if _locale(root) != "akomaNtoso":
        raise ValueError(f"radice inattesa: {_locale(root)!r}, atteso akomaNtoso")

    urn = ""
    eli = ""
    for alias in root.iter(_NS + "FRBRalias"):
        nome = alias.get("name") or ""
        if nome == "urn:nir":
            urn = (alias.get("value") or "").strip()
        elif nome == "eli":
            eli = (alias.get("value") or "").strip()
    if not urn:
        raise ValueError("manca FRBRalias name='urn:nir': atto non identificabile")

    titolo = _primo_testo(root, ("docTitle", "docPurpose", "shortTitle"))
    tipo = _primo_testo(root, ("docType",)).upper()

    # Numero e data si ricavano dalla URN, non da `docNumber` e `FRBRdate`: la URN è
    # l'identificatore su cui si regge tutta la pipeline, mentre `docNumber` porta a
    # volte rumore editoriale (un atto del 2026 dichiara "1 (Raccolta 2026)"), che
    # entrerebbe nel frontmatter e nel nome del file e impedirebbe di riconoscere
    # l'atto quando lo si confronta col corpus. I tag del documento restano da ripiego.
    numero_urn, data_urn = _numero_e_data_da_urn(urn)
    # Un atto non numerato (la Costituzione) ha URN senza numero e `docNumber` a zero:
    # meglio nessun numero che uno finto, che finirebbe nel nome del file e nelle citazioni.
    numero = numero_urn or _numero_docnumber(root)
    # La catena di ricadute per la data serve perché Normattiva dichiara `0000-00-00` in
    # FRBRWork per gli atti non numerati, e una data non valida nel frontmatter fa
    # fallire il parsing YAML dell'intero atto. L'alias ELI porta la data reale.
    data = _prima_data_valida(data_urn, _data_work(root), _data_da_eli(eli))

    # Il codice redazionale sta nell'alias ELI; se l'alias non lo espone si ripiega sul
    # codice fra parentesi in coda al titolo, che Normattiva vi mette sempre.
    codice = _codice_da_eli(eli) or _codice_da_titolo(titolo)

    # Data di consolidamento: la data dell'Expression, che per un export vigente è la
    # vigenza del testo restituito. Resta None se il documento non la dichiara, invece
    # di ripiegare sulla data di download, che non è un consolidamento.
    consolidato = _data_expression(root)

    corpo, n_art = _corpo(root, titolo)
    return AttoAkn(
        tipo=tipo,
        numero=numero,
        data=data,
        titolo=titolo,
        urn=urn,
        codice_redazionale=codice,
        consolidato_al=consolidato,
        corpo=corpo,
        n_articoli=n_art,
    )


def _primo_testo(root: ET.Element, tag_candidati: tuple[str, ...]) -> str:
    for tag in tag_candidati:
        for el in root.iter(_NS + tag):
            testo = _piatto(el)
            if testo:
                return testo
    return ""


def _numero_e_data_da_urn(urn: str) -> tuple[str, str]:
    """(numero, data ISO) dalla coda di una URN NIR `...:AAAA-MM-GG;numero`.

    Restituisce stringhe vuote se la URN non ha quella forma, per esempio perché è la
    URN della Costituzione, che non porta numero.
    """
    coda = (urn or "").rsplit(":", 1)[-1]
    m = re.match(r"^(?P<data>\d{4}-\d{2}-\d{2})(?:;(?P<num>[^~!]+))?", coda)
    if not m:
        return "", ""
    return (m.group("num") or "").strip(), m.group("data")


def _data_work(root: ET.Element) -> str:
    work = root.find(f".//{_NS}FRBRWork")
    if work is not None:
        d = work.find(_NS + "FRBRdate")
        if d is not None and d.get("date"):
            return d.get("date", "").strip()
    d = root.find(f".//{_NS}FRBRdate")
    return (d.get("date", "").strip() if d is not None else "")


def _data_expression(root: ET.Element) -> str | None:
    expr = root.find(f".//{_NS}FRBRExpression")
    if expr is None:
        return None
    d = expr.find(_NS + "FRBRdate")
    valore = (d.get("date") or "").strip() if d is not None else ""
    return valore or None


def _numero_docnumber(root: ET.Element) -> str:
    """`docNumber` come numero dell'atto, scartando lo zero degli atti non numerati."""
    valore = _primo_testo(root, ("docNumber",)).strip()
    return "" if valore in ("", "0") else valore


def _data_valida(d: str) -> str:
    """La data se è una data di calendario plausibile, altrimenti stringa vuota."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", (d or "").strip())
    if not m:
        return ""
    anno, mese, giorno = (int(x) for x in m.groups())
    if anno < 1000 or not 1 <= mese <= 12 or not 1 <= giorno <= 31:
        return ""
    return d.strip()


def _prima_data_valida(*candidati: str) -> str:
    for c in candidati:
        valida = _data_valida(c)
        if valida:
            return valida
    return ""


def _data_da_eli(eli: str) -> str:
    """Data dell'atto dall'alias ELI, che ha forma `eli/id/AAAA/MM/GG/CODICE/...`."""
    m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", eli or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def _codice_da_eli(eli: str) -> str:
    for parte in (eli or "").split("/"):
        if _CODICE_RE.match(parte.strip()):
            return parte.strip()
    return ""


def _codice_da_titolo(titolo: str) -> str:
    for m in re.finditer(r"\(([0-9A-Z]{7,9})\)", titolo or ""):
        if _CODICE_RE.match(m.group(1)):
            return m.group(1)
    return ""


def _corpo(root: ET.Element, titolo: str) -> tuple[str, int]:
    """Corpo Markdown dell'atto e numero di articoli trovati."""
    righe: list[str] = [f"# {titolo}".rstrip(), ""]

    # Formule di promulgazione, prima del primo articolo. Si prende il `preamble` e si
    # salta il `preface`: quest'ultimo contiene solo il blocco di metadati editoriali
    # (docType, docDate, docNumber, docTitle), che appiattito ripeterebbe il titolo già
    # emesso sopra. Verificato presente in tutti gli atti del campione di export.
    for el in root.iter(_NS + "preamble"):
        for r in _righe(el):
            righe += [r, ""]

    # Attenzione: un Element senza figli è falsy, quindi `find(a) or find(b)`
    # scarterebbe un `body` presente ma vuoto invece di usarlo.
    corpo_el = root.find(f".//{_NS}body")
    if corpo_el is None:
        corpo_el = root.find(f".//{_NS}mainBody")
    n_art = 0
    if corpo_el is not None:
        n_art = _scrivi(corpo_el, righe, 0)

    for el in root.iter(_NS + "conclusions"):
        for r in _righe(el):
            righe += [r, ""]

    # Allegati. Normattiva vi colloca contenuti che sono parte integrante dell'atto: le
    # diciotto disposizioni transitorie e finali della Costituzione sono tutte qui, fuori
    # dal `body`. Ignorarli le lascerebbe fuori dall'indice, cioè ricreerebbe a valle
    # esattamente il difetto del corpus a monte, che perde il contenuto quando sta in un
    # allegato. Ogni allegato diventa un chunk citabile per conto proprio (vedi
    # `ingest/parser.py`), invece di finire in coda all'ultimo articolo e farsi citare col
    # numero sbagliato.
    for attach in root.iter(_NS + "attachment"):
        for doc in attach.iter(_NS + "doc"):
            nome = (doc.get("name") or "").replace("-", " ").strip()
            corpo_all = doc.find(_NS + "mainBody")
            if corpo_all is None:
                continue
            contenuto = _righe(corpo_all)
            if not contenuto:
                continue
            righe += [f"## {nome or 'Allegato'}", ""]
            for r in contenuto:
                righe += [r, ""]

    return "\n".join(righe).strip() + "\n", n_art


def _scrivi(el: ET.Element, righe: list[str], n_art: int) -> int:
    """Attraversa il corpo emettendo intestazioni e testo; ritorna gli articoli visti."""
    for figlio in el:
        tag = _locale(figlio)
        if tag in ("num", "heading"):
            # Già consumati come etichetta dal contenitore o dall'articolo: emetterli di
            # nuovo qui duplicherebbe "Capo I" subito sotto la sua stessa intestazione.
            continue
        if tag in _CONTENITORI:
            etichetta = " ".join(
                x for x in (_testo_figlio(figlio, "num"), _testo_figlio(figlio, "heading")) if x
            ).strip()
            if etichetta:
                righe += [f"## {etichetta}", ""]
            n_art = _scrivi(figlio, righe, n_art)
        elif tag == "article":
            n_art += 1
            numero = _numero_articolo(_testo_figlio(figlio, "num"), n_art)
            rubrica, salta = _rubrica(figlio)
            # Forma `### Art. N. (Rubrica)`: la stessa già usata in data/codici-extra e
            # riconosciuta da ingest/parser.py.
            testa = f"### Art. {numero}."
            if rubrica:
                testa += f" ({rubrica})"
            righe += [testa, ""]
            for r in _righe(figlio, salta=salta):
                righe += [r, ""]
        elif tag in _TRASPARENTI or tag in _NUMERATI:
            for r in _righe(figlio):
                righe += [r, ""]
        elif tag in ("hcontainer", "division"):
            n_art = _scrivi(figlio, righe, n_art)
        else:
            testo = _piatto(figlio)
            if testo:
                righe += [testo, ""]
    return n_art


def _yaml_stringa(valore: str) -> str:
    """Scalare YAML fra doppi apici, con escaping: un titolo che contiene `: ` o un
    apice rompe il frontmatter e farebbe fallire l'ingestione dell'atto."""
    escaped = (valore or "").replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _frontmatter(a: AttoAkn) -> str:
    righe = [
        "---",
        f"tipo: {a.tipo}",
        f"numero: {_yaml_stringa(a.numero)}",
        # La data si scrive quotata, quindi come stringa e non come data YAML: il parser
        # del progetto la converte comunque in stringa, e così un valore anomalo della
        # fonte non fa più fallire il caricamento dell'intero frontmatter.
        f"data: {_yaml_stringa(a.data)}",
        f"titolo: {_yaml_stringa(a.titolo)}",
        f"urn: {a.urn}",
        f"codice_redazionale: {a.codice_redazionale}",
        "vigente: true",
        "fonte: Normattiva, API Open Data, export Akoma Ntoso",
    ]
    if a.consolidato_al:
        righe.append(f"consolidato_al: {a.consolidato_al}")
    righe += ["---", ""]
    return "\n".join(righe)
