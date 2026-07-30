"""Test della conversione Akoma Ntoso e del recupero da Normattiva.

La fixture `tests/fixtures-akn/legge-2026-101.akn.xml` è un export reale dell'API Open
Data di Normattiva (L. 8 giugno 2026, n. 101), tenuto fuori da `tests/fixtures/` perché
quella cartella viene indicizzata per intero dagli altri test.

Nessun test qui fa rete: la conversione è pura, e il pezzo che parla con la fonte è
verificato solo nelle sue parti pure (scomposizione della URN, selezione dei file
nell'archivio, lista bianca).
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from legal_consultant.fonte import akn, recupero
from legal_consultant.index import fts
from legal_consultant.ingest.parser import _split_chunks, parse_act

AKN = Path(__file__).parent / "fixtures-akn" / "legge-2026-101.akn.xml"


def _atto():
    return akn.converti(AKN.read_bytes())


def test_metadati_dall_akn():
    a = _atto()
    assert a.tipo == "LEGGE"
    assert a.numero == "101"
    assert a.data == "2026-06-08"
    assert a.urn == "urn:nir:stato:legge:2026-06-08;101"
    assert a.codice_redazionale == "26G00118"
    assert a.slug == "legge-2026-06-08-101"
    assert "Heysel" in a.titolo


def test_numero_dalla_urn_non_da_docnumber():
    """Il numero viene dalla URN: `docNumber` porta a volte rumore editoriale."""
    numero, data = akn._numero_e_data_da_urn("urn:nir:stato:legge:2026-01-07;1")
    assert (numero, data) == ("1", "2026-01-07")
    # Atto non numerato (la Costituzione): nessun numero, data presente.
    assert akn._numero_e_data_da_urn("urn:nir:stato:costituzione") == ("", "")


def test_data_non_valida_scartata():
    """Normattiva dichiara `0000-00-00` sugli atti non numerati: non deve finire nel
    frontmatter, perché una data impossibile fa fallire il parsing YAML dell'atto."""
    assert akn._data_valida("0000-00-00") == ""
    assert akn._data_valida("1947-12-27") == "1947-12-27"
    assert akn._prima_data_valida("0000-00-00", "", "1947-12-27") == "1947-12-27"
    assert akn._data_da_eli("eli/id/1947/12/27/047U0001/CONSOLIDATED/20231022") == "1947-12-27"


def test_markdown_leggibile_dal_parser_del_progetto(tmp_path):
    """Il Markdown prodotto deve passare per lo stesso parser del resto del corpus."""
    a = _atto()
    radice = tmp_path
    (radice / "Leggi").mkdir()
    f = radice / "Leggi" / f"{a.slug}.md"
    f.write_text(a.markdown(), encoding="utf-8")

    parsed = parse_act(f, radice)
    assert parsed.act.tipo == "LEGGE"
    assert parsed.act.numero == "101"
    assert parsed.act.urn == a.urn
    assert parsed.act.collezione == "Leggi"
    assert parsed.act.vigente is True

    articoli = [c for c in parsed.chunks if c.articolo]
    assert len(articoli) == a.n_articoli
    assert [c.articolo for c in articoli] == ["1", "2"]
    # Questo atto ha `heading` vuoto alla fonte e commi numerati dal primo: non ha
    # rubrica, e non se ne deve inventare una prendendo il primo comma.
    assert articoli[0].rubrica is None
    assert articoli[0].testo.startswith("1. ")


def _akn_sintetico(corpo_articolo: str, heading: str = "") -> bytes:
    """Documento Akoma Ntoso minimo, per esercitare un singolo comportamento."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
 <act name="monovigente">
  <meta><identification source="">
    <FRBRWork><FRBRdate date="2020-01-02" name=""/>
      <FRBRalias name="urn:nir" value="urn:nir:stato:legge:2020-01-02;7"/>
      <FRBRalias name="eli" value="eli/id/2020/01/02/20G00007/ORIGINAL"/>
    </FRBRWork>
  </identification></meta>
  <preface><p><docType>LEGGE</docType><docNumber>7</docNumber>
    <docTitle>Atto di prova. (20G00007)</docTitle></p></preface>
  <body><article eId="art_1"><num>Art. 1.</num><heading>{heading}</heading>
    {corpo_articolo}
  </article></body>
 </act>
</akomaNtoso>""".encode("utf-8")


def test_rubrica_esplicita_vince():
    a = akn.converti(_akn_sintetico(
        "<paragraph><num>1.</num><content><p>Testo del comma.</p></content></paragraph>",
        heading="Definizioni",
    ))
    assert "### Art. 1. (Definizioni)" in a.corpo


def test_rubrica_promossa_dal_capoverso_anonimo():
    """Con `heading` vuoto, un capoverso iniziale non numerato e seguito da commi è la
    rubrica: va promossa e non ripetuta nel corpo."""
    a = akn.converti(_akn_sintetico(
        "<paragraph><content><p>Ambito di applicazione</p></content></paragraph>"
        "<paragraph><num>1.</num><content><p>Testo del comma.</p></content></paragraph>"
    ))
    assert "### Art. 1. (Ambito di applicazione)" in a.corpo
    assert a.corpo.count("Ambito di applicazione") == 1


def test_capoverso_unico_non_e_rubrica():
    """Se quel capoverso è l'unico contenuto, È il testo dell'articolo: promuoverlo
    lascerebbe l'articolo indicizzato senza testo. Caso reale della Costituzione."""
    a = akn.converti(_akn_sintetico(
        "<paragraph><content><p>La forma repubblicana non puo' essere oggetto di "
        "revisione costituzionale.</p></content></paragraph>"
    ))
    assert "### Art. 1." in a.corpo
    assert "(La forma repubblicana" not in a.corpo
    assert "La forma repubblicana non puo'" in a.corpo


def test_numeri_di_comma_preservati():
    """I numeri di comma restano nel testo: senza, un comma non è più citabile."""
    a = _atto()
    assert "\n1. " in a.corpo or a.corpo.lstrip().startswith("1. ")


def test_note_escluse_dal_testo():
    """Il contenuto di authorialNote non entra nel corpo dell'articolo.

    Normattiva vi annida il testo integrale delle norme richiamate; indicizzarlo dentro
    l'articolo sposta il ranking verso l'articolo sbagliato.
    """
    a = _atto()
    grezzo = AKN.read_text(encoding="utf-8")
    assert "authorialNote" in grezzo, "la fixture deve contenere almeno una nota"
    assert "Entrata in vigore del provvedimento" not in a.corpo


def test_titolo_quotato_nel_frontmatter(tmp_path):
    """Un titolo con due punti o apici non deve rompere il frontmatter."""
    a = _atto()
    object.__setattr__(a, "titolo", 'Norme: "speciali" e altro')
    f = tmp_path / "x.md"
    (tmp_path / "Coll").mkdir()
    f = tmp_path / "Coll" / "x.md"
    f.write_text(a.markdown(), encoding="utf-8")
    parsed = parse_act(f, tmp_path)
    assert parsed.act.titolo == 'Norme: "speciali" e altro'


def test_allegato_e_unita_citabile_distinta():
    """Un allegato numerato apre un chunk proprio, per non essere citato col numero
    dell'ultimo articolo. Le disposizioni transitorie della Costituzione stanno lì."""
    corpo = (
        "## Art. 1. (Prima)\n\nTesto primo.\n\n"
        "## Art. 2. (Seconda)\n\nTesto secondo.\n\n"
        "## Allegato I\n\nDisposizioni transitorie e finali.\n"
    )
    chunks = _split_chunks(corpo)
    etichette = [c.articolo for c in chunks if c.articolo]
    assert etichette == ["1", "2", "Allegato I"]
    allegato = [c for c in chunks if c.articolo == "Allegato I"][0]
    assert "transitorie" in allegato.testo


def test_allegati_senza_numero_non_creano_chunk():
    """`## Allegati`, che compare nei codici come titolo di rassegna, resta testo."""
    chunks = _split_chunks("## Art. 1.\n\nTesto.\n\n## Allegati\n\nElenco.\n")
    assert [c.articolo for c in chunks if c.articolo] == ["1"]


def test_scomposizione_urn():
    assert recupero.scompone_urn("urn:nir:stato:legge:1978-05-22;194") == (
        "LEGGE", 1978, 194,
    )
    assert recupero.scompone_urn("urn:nir:stato:decreto.legge:2020-05-19;34") == (
        "DECRETO-LEGGE", 2020, 34,
    )
    denominazione, anno, numero = recupero.scompone_urn("urn:nir:stato:costituzione")
    assert denominazione == "COSTITUZIONE" and numero is None
    with pytest.raises(ValueError):
        recupero.scompone_urn("legge 194 del 1978")


def test_collezione_per_tipologia():
    assert recupero.collezione_per("LEGGE") == "Leggi"
    assert recupero.collezione_per("DECRETO-LEGGE") == "Decreti-legge"
    # Una tipologia non prevista non fa esplodere nulla e non inventa uno schema.
    assert recupero.collezione_per("ORDINANZA") == "Ordinanza"


def _zip_con(nomi_e_dati: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for nome, dati in nomi_e_dati.items():
            zf.writestr(nome, dati)
    return buf.getvalue()


def test_una_sola_versione_per_atto():
    """Se l'archivio porta più vigenze dello stesso atto si tiene la più recente."""
    z = _zip_con({
        "LEGGE_1/2026-01-01_A_VIGENZA_2020-01-01_V0.xml": b"<x/>",
        "LEGGE_1/2026-01-01_A_VIGENZA_2026-07-29_V0.xml": b"<x/>",
        "LEGGE_2/2026-01-02_B_VIGENZA_2026-07-29_V0.xml": b"<x/>",
    })
    with zipfile.ZipFile(io.BytesIO(z)) as zf:
        scelti = recupero._uno_per_atto(zf)
    assert len(scelti) == 2
    assert any("VIGENZA_2026-07-29" in s and "LEGGE_1" in s for s in scelti)
    assert not any("VIGENZA_2020-01-01" in s for s in scelti)


def test_lista_bianca_non_scrive_gli_atti_non_ammessi(tmp_path):
    """La lista bianca è un requisito di correttezza, non un'ottimizzazione: senza, una
    legge abrogata presente nell'export entrerebbe nell'indice come vigente."""
    dati = AKN.read_bytes()
    z = _zip_con({"LEGGE_101/2026-06-16_26G00118_VIGENZA_2026-07-29_V0.xml": dati})

    scritti, errori, saltati = recupero.scrivi_archivio(
        z, tmp_path, "LEGGE", solo_urn={"urn:nir:stato:legge:1999-01-01;1"}
    )
    assert scritti == [] and saltati == 1 and not errori

    scritti, errori, saltati = recupero.scrivi_archivio(
        z, tmp_path, "LEGGE", solo_urn={"urn:nir:stato:legge:2026-06-08;101"}
    )
    assert scritti == ["Leggi/legge-2026-06-08-101.md"] and saltati == 0 and not errori
    assert (tmp_path / "Leggi" / "legge-2026-06-08-101.md").is_file()


def test_xml_non_valido_segnalato_non_solleva(tmp_path):
    z = _zip_con({"LEGGE_1/2026-01-01_A_VIGENZA_2026-07-29_V0.xml": b"non xml"})
    scritti, errori, _ = recupero.scrivi_archivio(z, tmp_path, "LEGGE", solo_urn=None)
    assert scritti == [] and len(errori) == 1


def test_atto_recuperato_e_ricercabile(tmp_path):
    """Verifica di filiera: XML della fonte, Markdown, indice, ricerca."""
    a = _atto()
    (tmp_path / "Leggi").mkdir()
    f = tmp_path / "Leggi" / f"{a.slug}.md"
    f.write_text(a.markdown(), encoding="utf-8")

    conn = fts.connect(":memory:")
    if not fts.fts5_available(conn):
        pytest.skip("FTS5 non disponibile in questo build di SQLite")
    fts.init_db(conn)
    fts.insert_act(conn, parse_act(f, tmp_path))
    conn.commit()

    righe = fts.search(conn, "giornata nazionale in memoria", limit=5)
    assert righe, "l'atto recuperato deve essere trovabile"
    assert righe[0]["urn"] == a.urn
    assert fts.get_act(conn, urn=a.urn)
