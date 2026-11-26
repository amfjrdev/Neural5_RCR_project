"""Tests semaine 3 : extraction des modifications, versions dans le temps, ontologie.

Lancer : python -m pytest tests/test_week3.py -q
Les tests 1 à 10 n'utilisent pas la base ; les tests « base » utilisent data/jurideazor.sqlite
(après scripts/build_versions.py) et sont ignorés si les versions ne sont pas encore construites.
"""
import sqlite3
from pathlib import Path

import pytest

from jurideazor.amendments import expand_numbers, norm_num, parse_amendments
from jurideazor.ontology import concepts_of, sort_key_article
from jurideazor.versions import version_at

ROOT = Path(__file__).resolve().parents[1]

MODIF = """Article 1er. — La présente ordonnance a pour objet de modifier et de compléter la loi n° 90-11 du 21 avril 1990.
Art. 2. — L'article 44 de la loi n° 90-11 du 21 avril 1990 susvisée, est modifié, complété et rédigé comme suit :
"Art. 44. — La période supérieure à quinze (15) jours ouvrables équivaut à un (1) mois de travail".
Art. 3. — Les dispositions de la loi n° 90-11 du 21 avril 1990 susvisée sont complétées par un article 12 bis rédigé comme suit :
"Art. 12 bis. — L'inspecteur du travail s'assure que le contrat est conclu pour l'un des cas cités".
Art. 4. — L'article 13 de la loi n° 90-11 du 21 avril 1990 susvisée est complété par un alinéa 2, rédigé comme suit :
"Art. 13. — Les modalités d'application sont fixées par voie réglementaire".
Art. 5. — Toutes dispositions contraires sont abrogées notamment les articles 22 à 26 de la loi n° 90-11 du 21 avril 1990.
Art. 6. — La présente ordonnance sera publiée au Journal officiel.
"""


def test_norm_num():
    assert norm_num("12bis") == "12 bis"
    assert norm_num("73 - 4") == "73-4"
    assert norm_num("9]") == "9"


def test_expand_numbers():
    assert expand_numbers("22 à 26") == ["22", "23", "24", "25", "26"]
    assert expand_numbers("73-1, 73-2 et 73-3") == ["73-1", "73-2", "73-3"]
    assert expand_numbers("52 quater") == ["52 quater"]


def test_parse_operations():
    ops = {(o.action, o.target) for o in parse_amendments(MODIF)}
    assert ("modifie", "44") in ops
    assert ("cree", "12 bis") in ops
    assert ("complete", "13") in ops
    assert {("abroge", n) for n in ("22", "23", "24", "25", "26")} <= ops


def test_new_text_is_captured():
    op = next(o for o in parse_amendments(MODIF) if o.target == "44")
    assert op.new_text.startswith("Art. 44.") and "quinze (15)" in op.new_text


def test_quoted_article_is_not_a_source_article():
    """« "Art. 44. — » cité entre guillemets ne doit pas être pris pour un article du texte modificatif."""
    sources = [o.source_article for o in parse_amendments(MODIF)]
    assert "44" not in sources and "12" not in sources


def test_ocr_lost_target_uses_quoted_header():
    txt = ("Article 1er. — La présente ordonnance modifie la loi n° 90-11 du 21 avril 1990.\n"
           "Art. 6. 'arti a loi n° 90- avril 1990 susvisée est modifié et rédigé comme suit :\n"
           "\"Art. 42. — un congé supplémentaire ne pouvant être inférieur à dix (10) jours\".\n")
    assert ("modifie", "42") in {(o.action, o.target) for o in parse_amendments(txt)}


def test_terminology_change():
    txt = ("Article 1er. — La présente ordonnance modifie la loi n° 90-11 du 21 avril 1990.\n"
           "Art. 18. — Il est ajouté chaque fois après le terme . Convention collective, le terme accord collectif "
           "aux articles 115, 116 et 117 de la présente loi.\n")
    assert {o.target for o in parse_amendments(txt)} == {"115", "116", "117"}


def test_other_law_is_ignored():
    txt = "Article 1er. — La présente loi modifie la loi n° 90-02.\nArt. 2. — L'article 4 de la loi n° 90-02 est modifié comme suit : \"Art. 4. — x\".\n"
    assert parse_amendments(txt, law="90-11") == []


def test_concepts():
    assert "cdd" in concepts_of("Le contrat de travail peut être conclu pour une durée déterminée")
    assert "repos" in concepts_of("المادة 33 : ... الراحة الأسبوعية العادية يوم الجمعة")


def test_article_sort():
    assert sorted(["12 bis", "73-4", "12", "73", "9"], key=sort_key_article) == ["9", "12", "12 bis", "73", "73-4"]


# ---------- Tests sur la base (après build_versions.py) ----------
@pytest.fixture(scope="module")
def conn():
    db = ROOT / "data" / "jurideazor.sqlite"
    c = sqlite3.connect(db)
    if not c.execute("SELECT count(*) FROM relations WHERE relation='abroge'").fetchone()[0]:
        pytest.skip("lancer d'abord : python scripts/build_versions.py")
    return c


def test_version_1993_is_initial_and_flagged(conn):
    r = version_at(conn, "loi:90-11", "12", "1993-01-01")
    assert r["status"] == "en_vigueur" and r["version"]["valid_from"] == "1990-04-21"
    assert r["remplacee_depuis"] == "1996-07-10"


def test_current_version_comes_from_96_21(conn):
    r = version_at(conn, "loi:90-11", "12", "2020-01-01")
    assert r["version"]["source_number"] == "96-21" and r["remplacee_depuis"] is None


def test_abrogated_article_is_never_current(conn):
    r = version_at(conn, "loi:90-11", "22", "2000-01-01")
    assert r["status"] == "abrogee" and r["abroge_par"]["texte"] == "ordonnance:97-03"


def test_article_created_later_does_not_exist_before(conn):
    assert version_at(conn, "loi:90-11", "87 bis", "1993-01-01")["status"] == "inexistant"
    assert version_at(conn, "loi:90-11", "87 bis", "2000-01-01")["status"] == "en_vigueur"


def test_at_least_three_articles_with_several_versions(conn):
    n = conn.execute("""SELECT count(*) FROM (SELECT a.id FROM articles a JOIN article_versions v ON v.article_id=a.id
                        WHERE a.text_ref='loi:90-11' AND v.lang='fr' GROUP BY a.id HAVING count(*) >= 2)""").fetchone()[0]
    assert n >= 3  # critère du cahier des charges
