"""Colma le classi di atti che il corpus principale non contiene, dalla fonte ufficiale.

Uso:
    uv run python scripts/fetch_normattiva.py                    # tutte le classi mancanti
    uv run python scripts/fetch_normattiva.py --tipo LEGGE       # una sola tipologia
    uv run python scripts/fetch_normattiva.py --da 1990          # solo dal 1990 in poi
    uv run python scripts/fetch_normattiva.py --dry-run          # misura senza scaricare

Perche' esiste. Il corpus `italia-corpus` rispecchia il catalogo delle collezioni
preconfezionate di Normattiva, che non comprende la legge ordinaria: al 2026-07-29
mancavano 9.313 leggi non abrogate su 13.730, 1.584 decreti-legge non abrogati su 1.636 e
la Costituzione. La misura e la diagnosi sono in `docs/audit-completezza-corpus.md`.

Come. Si enumera dalla fonte, tipologia per tipologia e anno per anno, l'insieme degli
atti attesi; si confronta con le URN gia' presenti nell'indice; e per gli anni che hanno
lacune si chiede l'export asincrono in Akoma Ntoso, si converte nel Markdown del corpus e
si reindicizza in modo incrementale. Gli anni gia' completi si saltano senza scaricare
nulla, quindi il comando e' riavviabile: interrotto a metà, riprende da dove era.

Il traffico verso la fonte e' deliberatamente contenuto: una richiesta di export per anno
invece di due per atto, che sulle undicimila lacune misurate avrebbe significato
ventiduemila richieste. L'export asincrono e' la via documentata per lo scarico massivo.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from legal_consultant import update
from legal_consultant.config import INDEX_PATH, STATE_PATH, SUPPL_CORPUS_PATH, CORPUS_PATH
from legal_consultant.fonte import recupero
from legal_consultant.fonte.normattiva import (
    CLASSI_VIGENTI,
    Client,
    NormattivaError,
    NormattivaSovraccarico,
)
from legal_consultant.index import fts

# Le classi accertate come mancanti dall'audit.
#
# `per_anno` divide il recupero in un export per anno di emanazione, che è il modo di
# tenere ogni singola richiesta di dimensione ragionevole su tipologie da migliaia di atti.
#
# `lista_bianca` chiede di scrivere solo gli atti enumerati come non abrogati. Va tenuta
# attiva su tutto ciò che è numerato: l'export di un anno contiene anche le norme
# abrogate, e scriverle col frontmatter `vigente: true` sarebbe un errore peggiore della
# loro assenza. La Costituzione è l'unica eccezione, perché non ha numero né anno di
# provvedimento nella ricerca avanzata (la fonte li espone come zero) e quindi non è
# indirizzabile per URN costruita: è un atto unico e non abrogato, quindi si scrive
# quello che l'export restituisce.
CLASSI_MANCANTI = [
    {"tipo": "LEGGE", "classi": CLASSI_VIGENTI, "per_anno": True, "lista_bianca": True},
    {"tipo": "DECRETO-LEGGE", "classi": CLASSI_VIGENTI, "per_anno": True, "lista_bianca": True},
    {"tipo": "COSTITUZIONE", "classi": (None,), "per_anno": False, "lista_bianca": False},
]


def _log(msg: str) -> None:
    print(msg, flush=True)


def _enumera_attesi(client: Client, tipo: str, classi, da_anno: int | None):
    """Atti attesi dalla fonte per una tipologia, raggruppati per classe di provvedimento.

    Il raggruppamento serve a poter chiedere l'export per (anno, classe): un export senza
    filtro di classe contiene anche gli atti abrogati, che non vanno scritti, e sugli anni
    storici sono la maggioranza del volume scaricato.
    """
    per_classe: dict[str | None, list] = {}
    for classe in classi:
        refs = client.enumera(tipo, classe=classe)
        if da_anno:
            refs = [a for a in refs if a.anno.isdigit() and int(a.anno) >= da_anno]
        per_classe[classe] = refs
    return per_classe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tipo", action="append", help="tipologia da recuperare (ripetibile)")
    ap.add_argument("--da", type=int, default=None, help="anno minimo (default: tutti)")
    ap.add_argument("--dry-run", action="store_true", help="misura le lacune senza scaricare")
    ap.add_argument("--pausa", type=float, default=1.0, help="pausa fra le richieste, in secondi")
    ap.add_argument("--minuti", type=float, default=None,
                    help="budget di tempo: non avvia nuovi anni oltre questo limite")
    args = ap.parse_args(argv)

    if not Path(INDEX_PATH).exists():
        _log(f"Indice non trovato in {INDEX_PATH}. Esegui prima scripts/bootstrap_index.py.")
        return 1

    da_fare = CLASSI_MANCANTI
    if args.tipo:
        richiesti = {t.strip().upper() for t in args.tipo}
        da_fare = [c for c in CLASSI_MANCANTI if c["tipo"] in richiesti]
        if not da_fare:
            da_fare = [{"tipo": t, "classi": CLASSI_VIGENTI, "per_anno": True} for t in richiesti]

    client = Client(pausa=args.pausa)
    radice = Path(SUPPL_CORPUS_PATH)
    # Il recupero storico completo dura ore: con un budget si scarica quanto sta nel tempo
    # concesso e si lascia il resto al giro successivo. Il comando riparte sempre dalle
    # lacune residue, quindi ripetuti passaggi brevi convergono come uno lungo.
    scadenza = (time.monotonic() + args.minuti * 60) if args.minuti else None
    interrotto_per_tempo = False
    interrotto_per_fonte = False
    conn = fts.connect(INDEX_PATH)
    try:
        _log("Lettura delle URN già presenti nell'indice...")
        presenti = recupero.urn_presenti(conn)
        _log(f"  {len(presenti)} atti distinti già indicizzati.")

        totale_scritti = 0
        totale_chunk = 0
        errori: list[str] = []

        for voce in da_fare:
            if interrotto_per_fonte:
                break
            tipo = voce["tipo"]
            _log(f"\n=== {tipo} ===")
            try:
                attesi = _enumera_attesi(client, tipo, voce["classi"], args.da)
            except NormattivaError as e:
                errori.append(f"{tipo}: enumerazione fallita: {e}")
                _log(f"  ERRORE nell'enumerazione: {e}")
                continue

            tutti = [r for refs in attesi.values() for r in refs]
            mancanti_tot = recupero.refs_mancanti(tutti, presenti)
            _log(f"  attesi dalla fonte: {len(tutti)}   già presenti: "
                 f"{len(tutti) - len(mancanti_tot)}   mancanti: {len(mancanti_tot)}")
            if not mancanti_tot:
                continue
            if args.dry_run:
                for r in sorted(mancanti_tot, key=lambda x: (x.anno, x.numero))[:10]:
                    _log(f"    esempio: {tipo} {r.numero}/{r.anno}  {r.titolo[:70]}")
                continue

            # Un lavoro per ogni lotto contiguo di lacune, dentro ciascuna classe. Il costo
            # di un export è dominato dall'attesa di elaborazione presso la fonte, non dal
            # numero di atti, quindi pochi lotti grandi battono molti lotti piccoli; e il
            # filtro di classe evita di scaricare gli abrogati per poi scartarli.
            lavori: list[tuple[str | None, str | None, str | None, list]] = []
            for classe, refs in attesi.items():
                mancanti = recupero.refs_mancanti(refs, presenti)
                if not mancanti:
                    continue
                if not voce["per_anno"]:
                    lavori.append((classe, None, None, mancanti))
                    continue
                lavori += [
                    (classe, dal, al, gruppo)
                    for dal, al, gruppo in recupero.lotti_per_intervallo(mancanti)
                ]
            # Dal più recente al più antico: se il budget di tempo scade, quello che si è
            # già recuperato è la parte di normativa che si consulta di più.
            lavori.sort(key=lambda x: (x[1] or ""), reverse=True)

            for i, (classe, dal, al, attesi_lotto) in enumerate(lavori, 1):
                if scadenza is not None and time.monotonic() > scadenza:
                    interrotto_per_tempo = True
                    _log(f"  budget di {args.minuti:.0f} minuti esaurito: mi fermo a "
                         f"{i - 1}/{len(lavori)} lotti di {tipo}, il resto al prossimo giro.")
                    break
                etichetta = (
                    f"{dal}..{al} classe {classe}" if dal else f"tutto, classe {classe}"
                )
                # Lista bianca: solo le lacune di questo lotto. L'export ne contiene
                # comunque di più, e gli atti non attesi non vanno scritti come vigenti.
                da_scrivere = (
                    {r.urn for r in attesi_lotto} if voce.get("lista_bianca", True) else None
                )
                _log(f"  [{i}/{len(lavori)}] {etichetta}: chiedo l'export di "
                     f"{len(attesi_lotto)} atti...")
                try:
                    scritti, err, saltati = recupero.recupera_intervallo(
                        client, tipo, radice, da_scrivere, classe=classe, dal=dal, al=al,
                        su_avanzamento=recupero.stampa_avanzamento,
                    )
                except NormattivaSovraccarico as e:
                    # Il limite di traffico della fonte non riguarda questo lotto ma il
                    # client: insistere sui lotti successivi otterrebbe lo stesso rifiuto e
                    # consumerebbe il budget senza recuperare nulla. Si chiude il giro e si
                    # riprende alla prossima esecuzione, che è il modo in cui questo
                    # recupero è pensato per convergere.
                    errori.append(f"{tipo} {etichetta}: {e}")
                    _log(f"  [{i}/{len(lavori)}] {etichetta}: la fonte ha imposto un limite "
                         f"di traffico, interrompo il giro. ({e})")
                    interrotto_per_fonte = True
                    break
                except NormattivaError as e:
                    errori.append(f"{tipo} {etichetta}: {e}")
                    _log(f"  [{i}/{len(lavori)}] {etichetta}: ERRORE {e}")
                    continue

                errori += [f"{tipo} {etichetta}: {x}" for x in err]
                if scritti:
                    n = update.reindex_paths(conn, radice, scritti, [])
                    totale_chunk += n
                    totale_scritti += len(scritti)
                    presenti.update(
                        {r.urn for r in attesi_lotto}
                    )  # evita di riscaricarli in un rilancio nello stesso giro
                _log(f"  [{i}/{len(lavori)}] {etichetta}: {len(scritti)} atti scritti "
                     f"su {len(attesi_lotto)} attesi, {saltati} non attesi saltati, "
                     f"{len(err)} errori")
                time.sleep(args.pausa)

        if args.dry_run:
            _log("\n(dry-run: nulla è stato scaricato né scritto)")
            return 0

        n_atti, n_chunks = fts.corpus_stats(conn)
        commit, data = update.corpus_revision(CORPUS_PATH)
        update.write_state(STATE_PATH, commit, data, n_atti, n_chunks)
    finally:
        conn.close()

    _log(f"\nFatto: {totale_scritti} atti recuperati, {totale_chunk} chunk indicizzati, "
         f"{len(errori)} errori. Collezione: {radice}")
    if interrotto_per_tempo:
        _log("Recupero parziale per esaurimento del budget di tempo: rilanciare lo stesso "
             "comando riprende dalle lacune residue. `scripts/check_completezza.py` dice "
             "quanto resta.")
    if interrotto_per_fonte:
        _log("Recupero parziale perché la fonte ha imposto un limite di traffico su questo "
             "client: non è un errore del progetto e non richiede alcun intervento. Il "
             "recupero riprende da sé alla prossima esecuzione, tipicamente il giorno dopo "
             "con l'attività pianificata. `scripts/check_completezza.py` dice quanto resta.")
    if errori:
        _log("Errori (primi 20):")
        for e in errori[:20]:
            _log(f"  {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
