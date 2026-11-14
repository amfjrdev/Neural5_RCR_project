"""Nettoyage du texte brut extrait des PDF (français et arabe)."""
from __future__ import annotations

import re
import unicodedata

# --- En-têtes / pieds de page répétés du JO ------------------------------------
_RUNNING_FR = [
    re.compile(r"^\s*JOURNAL\s+OFFICIEL\s+DE\s+LA\s+REPUBLIQUE\s+ALGERIENNE.*$", re.I),
    re.compile(r"^\s*\d{1,2}\s+\w+\s+\d{4}\s*$"),          # date seule (en-tête)
    re.compile(r"^\s*\d{1,2}\s+\w+\s+\d{4}\s+JOURNAL\s+OFFICIEL.*$", re.I),
    re.compile(r"^\s*N°\s*\d{1,3}\s*$"),                      # « N° 17 » seul
    re.compile(r"^\s*\d{1,4}\s*$"),                           # numéro de page seul
]
_RUNNING_AR = [
    re.compile(r"^.*الجريدة\s+الرسمية\s+للجمهورية\s+الجزائرية.*$"),
    re.compile(r"^\s*العدد\s*\d{1,3}\s*$"),
    re.compile(r"^\s*\d{1,4}\s*$"),
]

_AR_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"
_EASTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def fix_mojibake(s: str) -> str:
    """Répare l'UTF-8 lu comme du Latin-1 (« Ã© » -> « é »), fréquent sur certains miroirs."""
    if "Ã" not in s and "â€" not in s:
        return s
    try:
        fixed = s.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        # réparation ligne par ligne, on garde l'original si ça échoue
        out = []
        for line in s.splitlines(keepends=True):
            try:
                out.append(line.encode("cp1252").decode("utf-8"))
            except (UnicodeEncodeError, UnicodeDecodeError):
                out.append(line)
        return "".join(out)


def normalize_unicode(s: str) -> str:
    # NFKC : ligatures (ﬁ -> fi) et formes de présentation arabes -> lettres de base
    s = unicodedata.normalize("NFKC", s)
    s = s.replace(" ", " ").replace("’", "'").replace("‘", "'")
    s = s.replace(_TATWEEL, "").translate(_EASTERN_DIGITS)
    return s


def remove_running_lines(lines: list[str], lang: str) -> list[str]:
    pats = _RUNNING_AR if lang == "ar" else _RUNNING_FR
    return [l for l in lines if not any(p.match(l) for p in pats)]


def dehyphenate(text: str) -> str:
    # « tra-\nvail » -> « travail » (seulement si la suite est en minuscule)
    return re.sub(r"(\w)-\n(\s*)([a-zà-ÿ])", r"\1\3", text)


def clean_page(text: str, lang: str) -> str:
    text = normalize_unicode(fix_mojibake(text))
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()]
    lines = remove_running_lines(lines, lang)
    text = "\n".join(lines)
    if lang == "fr":
        text = dehyphenate(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# --- Formes normalisées pour la comparaison (pas pour l'affichage) --------------
def fold_fr(s: str) -> str:
    """minuscules sans accents : 'Arrêté' -> 'arrete'."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def fold_ar(s: str) -> str:
    """Sans diacritiques, alifs unifiés, tā' marbūṭa -> hā', alif maqṣūra -> yā'."""
    s = _AR_DIACRITICS.sub("", s).replace(_TATWEEL, "")
    s = re.sub("[إأآٱ]", "ا", s)
    return s.replace("ة", "ه").replace("ى", "ي")
