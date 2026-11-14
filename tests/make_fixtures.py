"""Génère un faux numéro du JO (mise en page à deux colonnes) pour tester la chaîne
sans réseau : une version « PDF texte » et une version « scannée » (images seules).

Les contenus sont FICTIFS (marqués « texte de test ») : ils imitent la forme du JO,
pas son fond. Ne jamais les utiliser comme source juridique.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

W, H, M, GAP = 595, 842, 40, 20
COL_W = (W - 2 * M - GAP) / 2
FS = 9

HEADER = "JOURNAL OFFICIEL DE LA REPUBLIQUE ALGERIENNE N° 17"

PAGES = [
    {  # page 1 : sommaire
        "full": [HEADER, "SOMMAIRE"],
        "left": [
            "LOIS",
            "Loi n° 90-11 du 21 avril 1990 relative aux relations de travail .......... 2",
            "DECRETS",
            "Décret présidentiel du 18 avril 1990 portant nomination d'un directeur d'études .......... 3",
            "Décret exécutif n° 90-120 du 2 mai 1990 portant virement de crédits au sein du budget du ministère du travail .......... 3",
        ],
        "right": [
            "Décret exécutif n° 90-130 du 15 mai 1990 fixant les règles de la pêche côtière .......... 3",
            "ARRETES, DECISIONS ET AVIS",
            "Arrêté du 20 mai 1990 fixant les modalités d'organisation de l'inspection du travail .......... 3",
        ],
    },
    {  # page 2 : la loi
        "full": [HEADER, "LOIS"],
        "left": [
            "Loi n° 90-11 du 21 avril 1990 relative aux relations de travail.",
            "Le Président de la République,",
            "Vu la Constitution, notamment ses articles 52 et 53 ;",
            "Vu la loi n° 78-12 du 5 août 1978 relative au statut général du travailleur ;",
            "Après adoption par l'Assemblée populaire nationale,",
            "Promulgue la loi dont la teneur suit :",
            "TITRE I - OBJET ET CHAMP D'APPLICATION",
            "Article 1er. - La présente loi a pour objet de régir les relations individuelles et collectives de travail entre les travailleurs salariés et les employeurs (texte de test).",
            "Art. 2. - Sont considérés comme travailleurs salariés, au sens de la présente loi, toutes personnes qui fournissent un travail (texte de test).",
        ],
        "right": [
            "Art. 9. - Le contrat de travail est établi dans les formes qu'il convient aux parties d'adopter (texte de test).",
            "Art. 10. - La preuve du contrat de travail peut être faite par tout moyen (texte de test).",
            "Art. 73. - Le licenciement pour faute grave intervient dans le respect des procédures ; le préavis et le congé sont réglés par la loi (texte de test).",
            "La présente loi sera publiée au Journal officiel.",
            "Fait à Alger, le 21 avril 1990.",
        ],
    },
    {  # page 3 : décrets + arrêté
        "full": [HEADER, "DECRETS"],
        "left": [
            "Décret présidentiel du 18 avril 1990 portant nomination d'un directeur d'études.",
            "Par décret présidentiel du 18 avril 1990, M. Karim Exemple est nommé directeur d'études (texte de test).",
            "Décret exécutif n° 90-120 du 2 mai 1990 portant virement de crédits au sein du budget du ministère du travail.",
            "Le Chef du Gouvernement,",
            "Vu la loi n° 90-11 du 21 avril 1990 relative aux relations de travail ;",
            "Décrète :",
            "Article 1er. - Il est viré un crédit de cent mille dinars au budget de fonctionnement (texte de test).",
            "Décret exécutif n° 90-130 du 15 mai 1990 fixant les règles de la pêche côtière.",
            "Le Chef du Gouvernement,",
            "Vu le décret relatif au travail de la mer ;",
            "Décrète :",
            "Article 1er. - Le présent décret fixe les zones, les filets et les saisons de pêche côtière des navires (texte de test).",
        ],
        "right": [
            "MINISTERE DU TRAVAIL ET DES AFFAIRES SOCIALES",
            "Arrêté du 20 mai 1990 fixant les modalités d'organisation de l'inspection du travail.",
            "Le ministre du travail et des affaires sociales,",
            "Vu la loi n° 90-03 du 6 février 1990 relative à l'inspection du travail ;",
            "Arrête :",
            "Article 1er. - Le présent arrêté fixe l'organisation des services de l'inspection du travail et les visites des inspecteurs du travail chez les employeurs (texte de test).",
            "Art. 2. - L'inspecteur du travail contrôle l'application de la législation relative aux travailleurs et au salaire (texte de test).",
        ],
    },
]


def _write_column(page, x0, y0, lines, width):
    y = y0
    for line in lines:
        rect = pymupdf.Rect(x0, y, x0 + width, H - M)
        rest = page.insert_textbox(rect, line, fontsize=FS, fontname="helv")
        used = (H - M - y) - rest if rest >= 0 else H
        y += used + 6
    return y


def make_text_pdf(path: Path):
    doc = pymupdf.open()
    for spec in PAGES:
        page = doc.new_page(width=W, height=H)
        y = M
        for line in spec["full"]:
            page.insert_textbox(pymupdf.Rect(M, y, W - M, y + 24), line, fontsize=10, fontname="hebo", align=1)
            y += 24
        _write_column(page, M, y + 6, spec["left"], COL_W)
        _write_column(page, M + COL_W + GAP, y + 6, spec["right"], COL_W)
        page.insert_textbox(pymupdf.Rect(M, H - 34, W - M, H - 10), str(doc.page_count), fontsize=8, align=1)
    doc.save(path)


def make_scanned_pdf(src: Path, dst: Path, dpi: int = 200):
    """Version « scannée » : chaque page devient une image, sans couche texte."""
    out = pymupdf.open()
    with pymupdf.open(src) as doc:
        for p in doc:
            pix = p.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
            np_ = out.new_page(width=p.rect.width, height=p.rect.height)
            np_.insert_image(np_.rect, stream=pix.tobytes("png"))
    out.save(dst)


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures")
    d.mkdir(parents=True, exist_ok=True)
    make_text_pdf(d / "F1990017_test.pdf")
    make_scanned_pdf(d / "F1990017_test.pdf", d / "F1990017_scan_test.pdf")
    print("fixtures écrites dans", d)
