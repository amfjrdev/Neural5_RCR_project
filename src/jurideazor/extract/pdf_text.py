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


def _ordered_blocks(page, rtl: bool) -> str:
    """Ordonne les blocs en tenant compte des colonnes.

    Les blocs pleine largeur (titres de rubrique, en-têtes) servent de
    séparateurs ; entre deux séparateurs on lit une colonne entière puis l'autre.
    """
    w = page.rect.width
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
