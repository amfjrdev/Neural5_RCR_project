"""Tests de la semaine 1 (sans réseau) : python -m pytest -q"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from jurideazor.extract.clean import clean_page, fix_mojibake, fold_ar
from jurideazor.extract.pdf_text import extract_pages
from jurideazor.extract.segment import canonical_number, parse_date, segment_issue
from jurideazor.filter.labor import classify

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def fixtures():
    from make_fixtures import make_scanned_pdf, make_text_pdf
    FIX.mkdir(exist_ok=True)
    if not (FIX / "F1990017_test.pdf").exists():
        make_text_pdf(FIX / "F1990017_test.pdf")
    if not (FIX / "F1990017_scan_test.pdf").exists():
        make_scanned_pdf(FIX / "F1990017_test.pdf", FIX / "F1990017_scan_test.pdf")


def _segments(pdf, lang="fr", ocr=True):
    pages = extract_pages(pdf, lang, allow_ocr=ocr)
    return pages, segment_issue([(p.page_no, clean_page(p.text, lang)) for p in pages], lang)


EXPECTED = [  # (type, numéro, date, décision attendue)
    ("loi", "90-11", "1990-04-21", "keep"),
    ("decret_presidentiel", None, "1990-04-18", "reject"),
    ("decret_executif", "90-120", "1990-05-02", "reject"),
    ("decret_executif", "90-130", "1990-05-15", "reject"),
    ("arrete", None, "1990-05-20", "keep"),
]


@pytest.mark.parametrize("pdf", ["F1990017_test.pdf", "F1990017_scan_test.pdf"])
def test_segmentation_et_filtre_fr(pdf):
    pages, segs = _segments(FIX / pdf)
    if "scan" in pdf:
        assert all(p.method == "ocr" for p in pages)
    # le sommaire ne doit pas produire de textes
    got = [(s.text_type, s.text_number, s.sign_date,
            classify(s.title, s.body, s.section, s.text_type, "fr").relevance) for s in segs]
    assert got == EXPECTED


def test_visas_ne_comptent_pas():
    # « Vu ... travail » dans un décret sur la pêche ne doit pas le rendre pertinent
    d = classify("Décret exécutif n° 90-130 du 15 mai 1990 fixant les règles de la pêche côtière.",
                 "Vu la loi n° 90-11 relative aux relations de travail ;\nVu le code du travail ;\n"
                 "Article 1er. - Le présent décret fixe les zones de pêche.", None, "decret_executif", "fr")
    assert d.relevance == "reject"


def test_circulaire_signalee():
    d = classify("Circulaire du 3 mars 2010 relative au contrat de travail à durée déterminée", "texte",
                 None, "circulaire", "fr")
    assert d.relevance == "keep" and d.is_circular


def test_mojibake():
    assert fix_mojibake("relative aux relations de travail, arrÃªtÃ© du ministÃ¨re") == \
        "relative aux relations de travail, arrêté du ministère"


# ------------------------------------------------------------------- arabe ---
AR_PAGE = """الجريدة الرسمية للجمهورية الجزائرية / العدد 17
فهرس
قوانين
قانون رقم 90-11 مؤرّخ في 26 رمضان عام 1410 الموافق 21 أبريل سنة 1990، يتعلّق بعلاقات العمل.
إنّ رئيس الجمهوريّة،
- بناءً على الدّستور،
المادّة الأولى: يهدف هذا القانون إلى تنظيم علاقات العمل الفرديّة والجماعيّة بين العمّال الأجراء والمستخدمين (نص تجريبي).
مراسيم
مرسوم رئاسيّ مؤرّخ في 22 رمضان عام 1410 الموافق 18 أبريل سنة 1990، يتضمّن تعيين مدير دراسات.
بموجب مرسوم رئاسيّ مؤرّخ في 18 أبريل سنة 1990 يعيّن السّيّد كريم مثال مديرا للدراسات (نص تجريبي).
مرسوم تنفيذيّ رقم 130-90 مؤرّخ في 20 شوّال عام 1410 الموافق 15 مايو سنة 1990، يحدّد قواعد الصّيد السّاحلي.
إنّ رئيس الحكومة،
- وبمقتضى القانون رقم 90-11 المتعلّق بعلاقات العمل،
المادّة الأولى: يحدّد هذا المرسوم مناطق الصّيد السّاحلي ومواسمه (نص تجريبي).
"""


def test_segmentation_et_filtre_ar():
    segs = segment_issue([(1, clean_page(AR_PAGE, "ar"))], "ar")
    got = [(s.text_type, s.text_number, s.sign_date,
            classify(s.title, s.body, s.section, s.text_type, "ar").relevance) for s in segs]
    assert got == [
        ("loi", "90-11", "1990-04-21", "keep"),
        ("decret_presidentiel", None, "1990-04-18", "reject"),
        ("decret_executif", "90-130", "1990-05-15", "reject"),  # numéro inversé remis dans l'ordre
    ]


def test_numero_et_date():
    assert canonical_number("11-90", "1990-04-21") == "90-11"
    assert canonical_number("90-11", "1990-04-21") == "90-11"
    assert parse_date("Décret exécutif n° 97-59 du Aouel Dhou El Kaada 1417 correspondant au 9 mars 1997", "fr") == "1997-03-09"
    assert parse_date("Ordonnance n° 96-21 du 1er juillet 1996", "fr") == "1996-07-01"
    assert fold_ar("المادّة الأولى") == "الماده الاولي"


# -------------------------------------------------- chaîne complète + rejeu ---
def test_chaine_rejouable_et_evaluation(tmp_path, monkeypatch):
    import yaml
    from jurideazor import cli
    from jurideazor.config import ROOT

    cfg = yaml.safe_load((ROOT / "config" / "config.example.yaml").read_text(encoding="utf-8"))
    cfg["paths"]["data_dir"] = str(tmp_path / "data")
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    pdf = tmp_path / "in.pdf"
    shutil.copyfile(FIX / "F1990017_test.pdf", pdf)

    def run(*args):
        cli.main(["--config", str(cfg_path), *args])

    for _ in range(2):  # deux passages complets : aucun doublon
        run("import-pdf", str(pdf), "--year", "1990", "--number", "17", "--edition", "fr")
        run("process")
    from jurideazor.db import connect
    conn = connect(tmp_path / "data" / "jurideazor.sqlite")
    assert conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM texts").fetchone()[0] == 5
    row = conn.execute("SELECT source_url FROM texts WHERE text_number='90-11'").fetchone()
    assert row["source_url"].endswith("/FTP/jo-francais/1990/F1990017.pdf")  # provenance gardée

    sample = tmp_path / "sample.csv"
    run("sample-filter", "--n", "5", "--out", str(sample))
    rows = list(csv.DictReader(open(sample, encoding="utf-8")))
    for r in rows:  # annotation « humaine » simulée
        r["gold"] = "keep" if ("travail" in r["title"] and "crédits" not in r["title"]) else "reject"
    with open(sample, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    report = tmp_path / "report.md"
    run("eval-filter", "--csv", str(sample), "--out", str(report))
    assert "Précision | 1.00" in report.read_text(encoding="utf-8")
    # l'annotation survit à un retraitement
    run("process")
    assert conn.execute("SELECT COUNT(*) FROM texts WHERE gold_label IS NOT NULL").fetchone()[0] == 5
