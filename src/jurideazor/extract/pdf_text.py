"""PDF -> texte, page par page.

- PDF natif (>= 2002) : PyMuPDF, avec remise en ordre des deux colonnes du JO
  (gauche puis droite en français, droite puis gauche en arabe) ;
- page scannée (texte quasi vide) : OCR Tesseract ('fra' ou 'ara').
La méthode utilisée est conservée pour chaque page (traçabilité).
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import pymupdf


@dataclass
class PageText:
    page_no: int      # 1-based
    text: str
    method: str       # 'text' | 'ocr' | 'empty'


_SWAP_PARENS = str.maketrans("()", ")(")


def join_rtl_fragments(frags: list[tuple[float, float, float, float, str]]) -> str:
    """Recolle les morceaux d'un bloc arabe en lignes visuelles.

    Dans les PDF arabes du JO, chaque ligne est stockée en plusieurs morceaux, coupés à
    chaque changement de sens d'écriture (donc à chaque nombre) :
        « مرسوم رئاسي رقم 24 » | « - » | « 432 » | « مؤرّخ في 29 » ...
    Lus tels quels, ces morceaux donnent une ligne par morceau et le numéro du texte est
    perdu. On regroupe ici les morceaux posés sur la même ligne de base, on les lit de
    droite à gauche, et on ne met une espace que là où la page en montre une.

    frags : [(x0, y0, x1, y1, texte)] -> lignes séparées par « \\n ».
    Les parenthèses sont remises dans l'ordre logique : le PDF donne le glyphe affiché,
    qui est inversé en écriture de droite à gauche.
    """
    rows: list[tuple[float, list]] = []
    for f in sorted(frags, key=lambda f: ((f[1] + f[3]) / 2, -f[2])):
        mid = (f[1] + f[3]) / 2
        if rows and abs(rows[-1][0] - mid) <= max(2.0, 0.3 * (f[3] - f[1])):
            rows[-1][1].append(f)
        else:
            rows.append((mid, [f]))
    lines = []
    for _, row in rows:
        row.sort(key=lambda f: -f[2])                     # de droite à gauche
        text, prev = "", None
        for f in row:
            piece = f[4]
            if prev is not None and text and piece and not text[-1].isspace() and not piece[0].isspace():
                if prev[0] - f[2] > 0.25 * (f[3] - f[1]):   # un blanc visible entre les deux
                    text += " "
            text += piece
            prev = f
        lines.append(text.translate(_SWAP_PARENS))
    return "\n".join(lines)


def _rtl_blocks(page) -> list[tuple]:
    """Blocs de texte d'une page arabe, au même format que get_text("blocks"),
    mais avec les lignes recollées par join_rtl_fragments."""
    blocks = []
    for n, blk in enumerate(page.get_text("dict")["blocks"]):
        if blk.get("type") != 0:
            continue
        frags = []
        for line in blk["lines"]:
            t = "".join(s["text"] for s in line["spans"])
            if t.strip():
                frags.append((*line["bbox"], t))
        if frags:
            x0, y0, x1, y1 = blk["bbox"]
            blocks.append((x0, y0, x1, y1, join_rtl_fragments(frags), n, 0))
    return blocks


def _ordered_blocks(page, rtl: bool) -> str:
    """Ordonne les blocs en tenant compte des colonnes.

    Les blocs pleine largeur (titres de rubrique, en-têtes) servent de
    séparateurs ; entre deux séparateurs on lit une colonne entière puis l'autre.
    """
    w = page.rect.width
    if rtl:
        blocks = _rtl_blocks(page)
    else:
        blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    blocks.sort(key=lambda b: (round(b[1], 1), b[0]))
    mid = w / 2
    out, left, right = [], [], []

    def flush():
        cols = (right, left) if rtl else (left, right)
        for col in cols:
            out.extend(b[4] for b in sorted(col, key=lambda b: b[1]))
        left.clear(), right.clear()

    for b in blocks:
        x0, x1 = b[0], b[2]
        # Le texte en colonnes ne franchit jamais la gouttière centrale : un bloc qui
        # la franchit est pleine largeur ou centré (en-tête, rubrique « LOIS »...).
        if x0 < mid < x1:
            flush()
            out.append(b[4])
        elif (x0 + x1) / 2 < mid:
            left.append(b)
        else:
            right.append(b)
    flush()
    return "\n".join(t.rstrip() for t in out)


def _ocr_page(page, lang: str, dpi: int) -> str:
    import pytesseract
    from PIL import Image

    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    # psm 3 : segmentation automatique, gère les deux colonnes
    return pytesseract.image_to_string(img, lang="ara" if lang == "ar" else "fra", config="--psm 3")


def extract_pages(pdf_path, lang: str, ocr_min_chars: int = 80, dpi: int = 300,
                  allow_ocr: bool = True) -> list[PageText]:
    pages: list[PageText] = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            txt = _ordered_blocks(page, rtl=(lang == "ar"))
            if len(txt.strip()) >= ocr_min_chars:
                pages.append(PageText(i, txt, "text"))
                continue
            if allow_ocr:
                ocr = _ocr_page(page, lang, dpi)
                if ocr.strip():
                    pages.append(PageText(i, ocr, "ocr"))
                    continue
            pages.append(PageText(i, txt, "empty" if not txt.strip() else "text"))
    return pages
