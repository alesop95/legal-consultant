"""Controllo di completezza del corpus: fallisce dicendo cosa manca.

Uso:
    uv run python scripts/check_completezza.py             # controllo completo
    uv run python scripts/check_completezza.py --offline   # solo le sentinelle, senza rete
    uv run python scripts/check_completezza.py --quiet     # solo il verdetto

Codici di uscita: 0 se il corpus e' completo secondo entrambi i controlli, 1 se ci sono
lacune, 2 se il controllo non ha potuto girare (indice assente, fonte irraggiungibile).

Perche' esiste. Il difetto che questo controllo intercetta non e' l'incompletezza in se',
ma l'incompletezza SILENZIOSA: fino al 2026-07-29 il corpus dichiarava 287.805 atti e
sync completo mentre gli mancavano 9.313 leggi vigenti, e nulla nel prodotto lo diceva.
Un numero grande non e' una garanzia, quindi questo comando non stampa un totale
rassicurante: stampa quale classe manca e quale atto atteso non si trova, e ritorna un
codice di errore.

I due controlli sono indipendenti per costruzione, perche' uno solo non basterebbe.

Il primo e' dall'alto: chiede alla fonte quali tipologie di atto esistono e quanti atti
ha ciascuna, e le confronta con l'indice. L'elenco delle tipologie viene ricavato
dall'API di Normattiva a ogni esecuzione e non e' cablato qui: cablarlo ripeterebbe
esattamente l'errore che ha prodotto la lacuna, cioe' fidarsi di un elenco di cio' che
c'e' per stabilire cio' che dovrebbe esserci.

Il secondo e' dal basso: una lista di atti notori, scelti perche' uno studio legale li
consulta davvero, verificati uno per uno nell'indice. E' il controllo che ha scoperto il
problema in partenza, ed e' piu' affidabile di qualunque conteggio, perche' una collezione
puo' esistere ed essere popolata solo in parte. Se i due controlli divergono, ha ragione
questo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from legal_consultant.config import INDEX_PATH
from legal_consultant.fonte.normattiva import Client, NormattivaError
from legal_consultant.index import fts

# Atti sentinella: (tipo nel frontmatter, numero, anno, descrizione).
# Criterio di scelta: atti che uno studio legale consulta nella pratica quotidiana,
# distribuiti su classi diverse, e in particolare quelli la cui assenza era invisibile
# perche' la ricerca per parole chiave restituiva comunque qualcosa di pertinente al tema
# (il regolamento attuativo, l'atto che li modifica, una norma omonima). Le prime sei
# sono quelle con cui la lacuna e' stata scoperta dall'esterno.
SENTINELLE = [
    ("LEGGE", "194", 1978, "Interruzione volontaria di gravidanza"),
    ("LEGGE", "184", 1983, "Adozione e affidamento"),
    ("LEGGE", "219", 2017, "Consenso informato e DAT"),
    ("LEGGE", "833", 1978, "Istituzione del Servizio sanitario nazionale"),
    ("LEGGE", "40", 2004, "Procreazione medicalmente assistita"),
    ("LEGGE", "405", 1975, "Consultori familiari"),
    ("LEGGE", "24", 2017, "Responsabilita' sanitaria (Gelli-Bianco)"),
    ("LEGGE", "241", 1990, "Procedimento amministrativo"),
    ("LEGGE", "300", 1970, "Statuto dei lavoratori"),
    ("LEGGE", "604", 1966, "Licenziamenti individuali"),
    ("LEGGE", "898", 1970, "Divorzio"),
    ("LEGGE", "91", 1992, "Cittadinanza"),
    ("LEGGE", "104", 1992, "Legge quadro handicap"),
    ("LEGGE", "76", 2016, "Unioni civili"),
    ("LEGGE", "431", 1998, "Locazioni abitative"),
    ("LEGGE", "633", 1941, "Diritto d'autore"),
    ("LEGGE", "689", 1981, "Sanzioni amministrative"),
    ("LEGGE", "69", 2019, "Codice rosso"),
    ("LEGGE", "3", 2019, "Reati contro la pubblica amministrazione"),
    ("LEGGE", "68", 2015, "Delitti ambientali"),
    ("DECRETO-LEGGE", "34", 2020, "Decreto Rilancio"),
    ("DECRETO-LEGGE", "6", 2020, "Misure urgenti COVID-19"),
    ("COSTITUZIONE", "", 1947, "Costituzione della Repubblica italiana"),
    ("DECRETO LEGISLATIVO", "231", 2001, "Responsabilita' degli enti"),
    ("DECRETO LEGISLATIVO", "81", 2008, "Sicurezza sul lavoro"),
    ("DECRETO LEGISLATIVO", "196", 2003, "Codice privacy"),
    ("DECRETO LEGISLATIVO", "152", 2006, "Codice dell'ambiente"),
    ("DECRETO LEGISLATIVO", "36", 2023, "Codice dei contratti pubblici"),
    ("DECRETO LEGISLATIVO", "206", 2005, "Codice del consumo"),
    ("DECRETO LEGISLATIVO", "285", 1992, "Codice della strada"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "380", 2001, "Testo unico edilizia"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "309", 1990, "Testo unico stupefacenti"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "447", 1988, "Codice di procedura penale"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "917", 1986, "TUIR"),
    ("REGIO DECRETO", "262", 1942, "Codice civile"),
    ("REGIO DECRETO", "1398", 1930, "Codice penale"),
    ("REGIO DECRETO", "1443", 1940, "Codice di procedura civile"),
    ("LEGGE COSTITUZIONALE", "3", 2001, "Riforma del Titolo V"),
    # Compravendita immobiliare residenziale. E' la materia su cui un privato consulta
    # per primo uno strumento come questo, e attraversa fisco, edilizia, pubblicita'
    # immobiliare e contratto: senza queste sentinelle il corpus poteva risultare
    # completo pur non contenendo la norma che rende nullo l'atto di vendita.
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "131", 1986, "TU imposta di registro, agevolazione prima casa"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "601", 1973, "Imposta sostitutiva sui finanziamenti"),
    ("DECRETO LEGISLATIVO", "122", 2005, "Tutela acquirenti di immobili da costruire"),
    ("DECRETO LEGISLATIVO", "23", 2011, "Cedolare secca sulle locazioni"),
    ("DECRETO LEGISLATIVO", "192", 2005, "Prestazione energetica degli edifici, APE"),
    ("DECRETO LEGISLATIVO", "504", 1992, "Base imponibile ICI, ancora richiamata dall'IMU"),
    ("DECRETO-LEGGE", "50", 2017, "Locazioni brevi"),
    ("DECRETO-LEGGE", "69", 2024, "Salva Casa, tolleranze e stato legittimo"),
    ("LEGGE", "160", 2019, "Disciplina dell'IMU"),
    ("LEGGE", "266", 2005, "Prezzo-valore, art. 1 comma 497"),
    ("LEGGE", "47", 1985, "Condono edilizio, menzioni urbanistiche in atto"),
    ("LEGGE", "52", 1985, "Pubblicita' immobiliare, conformita' catastale in atto"),
    ("LEGGE", "448", 1998, "Credito d'imposta per riacquisto della prima casa"),
]

# Un atto presente ma privo di articolato non e' un atto presente: il codice penale nel
# corpus a monte e' un guscio di quattro chunk con la sola formula di approvazione.
#
# La misura, pero', non puo' essere il numero di chunk. Le leggi finanziarie sono
# formalmente composte da un solo articolo con centinaia di commi, e finiscono
# nell'indice come due o tre chunk pur contenendo tutto: la legge 266/2005, che porta la
# regola del prezzo-valore, sta in due chunk e mezzo milione di caratteri. Un criterio a
# chunk le dichiarerebbe vuote, che e' il falso positivo peggiore per un controllo la cui
# ragione d'essere e' non dare falsa sicurezza. Si misurano quindi i caratteri, che sono
# cio' che conta davvero, e i chunk restano solo un'informazione a video.
_MIN_CARATTERI_ARTICOLATO = 20_000
_ARTICOLATI = {
    ("REGIO DECRETO", "262"), ("REGIO DECRETO", "1398"), ("REGIO DECRETO", "1443"),
    ("DECRETO LEGISLATIVO", "81"), ("DECRETO LEGISLATIVO", "152"),
    ("DECRETO LEGISLATIVO", "206"), ("DECRETO LEGISLATIVO", "285"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "380"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "309"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "447"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "131"),
    ("DECRETO DEL PRESIDENTE DELLA REPUBBLICA", "601"),
    ("DECRETO LEGISLATIVO", "122"), ("DECRETO LEGISLATIVO", "192"),
    ("DECRETO LEGISLATIVO", "504"), ("DECRETO-LEGGE", "50"), ("DECRETO-LEGGE", "69"),
    ("LEGGE", "266"), ("LEGGE", "194"), ("LEGGE", "184"), ("LEGGE", "833"),
    ("LEGGE", "241"), ("LEGGE", "300"), ("DECRETO-LEGGE", "34"), ("COSTITUZIONE", ""),
}

# Copertura minima accettabile per tipologia, sotto la quale la classe e' considerata in
# lacuna. Non e' una soglia di comodo: l'audit del 2026-07-29 ha misurato le tipologie
# realmente coperte fra il 99,3% e il 100%, quindi una caduta sotto il 95% e' un segnale
# di regressione e non rumore statistico. Le tipologie storiche minori, dove pochi atti
# di scarto producono percentuali ballerine, sono escluse dalla soglia con una
# dimensione minima.
_COPERTURA_MINIMA = 0.95
_DIMENSIONE_MINIMA = 100


def _indice_corpus(conn) -> dict[tuple[str, str, str], tuple[int, int]]:
    """(tipo, numero, anno) -> (numero di chunk, caratteri totali) per ogni atto."""
    out: dict[tuple[str, str, str], tuple[int, int]] = {}
    sql = (
        "SELECT tipo, numero, data, COUNT(*), COALESCE(SUM(LENGTH(testo)), 0) "
        "FROM chunks GROUP BY tipo, numero, data"
    )
    for tipo, numero, data, n, caratteri in conn.execute(sql):
        anno = str(data or "")[:4]
        chiave = ((tipo or "").strip().upper(), str(numero or "").strip(), anno)
        chunk_precedenti, caratteri_precedenti = out.get(chiave, (0, 0))
        out[chiave] = (chunk_precedenti + int(n), caratteri_precedenti + int(caratteri or 0))
    return out


def _conteggi_corpus(conn) -> dict[str, int]:
    """tipo -> atti distinti per URN nell'indice."""
    out: dict[str, int] = {}
    sql = "SELECT tipo, COUNT(DISTINCT urn) FROM chunks GROUP BY tipo"
    for tipo, n in conn.execute(sql):
        out[(tipo or "").strip().upper()] = int(n)
    return out


def _controllo_sentinelle(conn, quiet: bool) -> list[str]:
    """Verifica le sentinelle una per una. Ritorna la lista dei problemi trovati."""
    atti = _indice_corpus(conn)
    problemi: list[str] = []
    if not quiet:
        print("Controllo dal basso: atti sentinella")
        print(f"  {'ESITO':<12} {'ATTO':<34} {'CHUNK':>6} {'CARATTERI':>10}  DESCRIZIONE")
    for tipo, numero, anno, descrizione in SENTINELLE:
        chiave = (tipo, numero, str(anno))
        misura = atti.get(chiave)
        etichetta = f"{tipo.split()[0].title()} {numero}/{anno}".replace(" /", " ")
        if misura is None:
            n, caratteri = None, None
            esito = "ASSENTE"
            problemi.append(f"atto atteso assente: {tipo} n. {numero} del {anno} ({descrizione})")
        else:
            n, caratteri = misura
            if (tipo, numero) in _ARTICOLATI and caratteri < _MIN_CARATTERI_ARTICOLATO:
                esito = "SENZA TESTO"
                problemi.append(
                    f"atto presente ma senza articolato: {tipo} n. {numero} del {anno} "
                    f"({descrizione}): {caratteri} caratteri, attesi almeno "
                    f"{_MIN_CARATTERI_ARTICOLATO}"
                )
            else:
                esito = "ok"
        if not quiet:
            print(
                f"  {esito:<12} {etichetta:<34} {str(n if n is not None else '-'):>6} "
                f"{str(caratteri if caratteri is not None else '-'):>10}  {descrizione}"
            )
    return problemi


def _controllo_tipologie(conn, quiet: bool) -> tuple[list[str], list[str]]:
    """Confronta i conteggi per tipologia con la fonte. Ritorna (problemi, avvisi)."""
    client = Client()
    tipologie = client.tipologie()
    corpus = _conteggi_corpus(conn)
    problemi: list[str] = []
    avvisi: list[str] = []
    if not quiet:
        print("\nControllo dall'alto: tipologie di atto dichiarate da Normattiva")
        print(f"  {'TIPOLOGIA':<52} {'FONTE':>8} {'CORPUS':>8} {'COPERTURA':>10}")
    for tipologia in tipologie:
        atteso = client.conta(tipologia)
        presente = corpus.get(tipologia.strip().upper(), 0)
        copertura = (presente / atteso) if atteso else 1.0
        nota = ""
        if atteso and presente == 0:
            problemi.append(f"tipologia interamente assente: {tipologia} ({atteso} atti alla fonte)")
            nota = "  <== ASSENTE"
        elif atteso >= _DIMENSIONE_MINIMA and copertura < _COPERTURA_MINIMA:
            problemi.append(
                f"tipologia in lacuna: {tipologia}: {presente} su {atteso} "
                f"({copertura * 100:.1f}%, minimo {_COPERTURA_MINIMA * 100:.0f}%)"
            )
            nota = "  <== LACUNA"
        elif atteso and copertura < _COPERTURA_MINIMA:
            avvisi.append(
                f"tipologia minore sotto soglia, non bloccante: {tipologia}: "
                f"{presente} su {atteso}"
            )
        if not quiet:
            print(f"  {tipologia[:52]:<52} {atteso:>8} {presente:>8} "
                  f"{copertura * 100:>9.1f}%{nota}")
    return problemi, avvisi


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--offline", action="store_true",
                    help="salta il confronto con la fonte, verifica solo le sentinelle")
    ap.add_argument("--quiet", action="store_true", help="stampa solo il verdetto")
    args = ap.parse_args(argv)

    if not Path(INDEX_PATH).exists():
        print(f"CONTROLLO NON ESEGUIBILE: indice non trovato in {INDEX_PATH}.")
        return 2

    conn = fts.connect(INDEX_PATH)
    try:
        problemi = _controllo_sentinelle(conn, args.quiet)
        avvisi: list[str] = []
        if not args.offline:
            try:
                p, a = _controllo_tipologie(conn, args.quiet)
                problemi += p
                avvisi += a
            except NormattivaError as e:
                print(f"\nCONTROLLO PARZIALE: la fonte non risponde ({e}).")
                print("Le sentinelle sono state verificate; il confronto per tipologia no.")
                if problemi:
                    _stampa_problemi(problemi, avvisi)
                    return 1
                return 2
    finally:
        conn.close()

    _stampa_problemi(problemi, avvisi)
    return 1 if problemi else 0


def _stampa_problemi(problemi: list[str], avvisi: list[str]) -> None:
    print()
    if avvisi:
        print(f"Avvisi non bloccanti ({len(avvisi)}):")
        for a in avvisi:
            print(f"  - {a}")
        print()
    if not problemi:
        print("ESITO: corpus completo secondo entrambi i controlli.")
        return
    print(f"ESITO: CORPUS INCOMPLETO. {len(problemi)} lacune.")
    for p in problemi:
        print(f"  - {p}")
    print()
    print("Rimedio: `uv run python scripts/fetch_normattiva.py` per le classi mancanti,")
    print("oppure `uv run python scripts/fetch_atto.py <urn>` per un singolo atto.")


if __name__ == "__main__":
    sys.exit(main())
