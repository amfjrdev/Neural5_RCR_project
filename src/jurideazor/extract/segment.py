"""Découpage d'un numéro du JO en textes juridiques, avec leurs métadonnées.

Un numéro contient un sommaire puis des dizaines de textes. Un texte commence par
un intitulé du type « Décret exécutif n° 97-59 du ... correspondant au 9 mars 1997
déterminant ... ». Pour distinguer un vrai début de texte d'une ligne du sommaire
ou d'une citation, on exige :
  1. un intitulé en début de ligne, avec majuscule (FR) ;
  2. pas de points de conduite + numéro de page (= ligne de sommaire) ;
  3. un marqueur de préambule peu après (« Le Président de la République », « Vu »,
     « Par décret », « Article 1er »...), avant tout autre intitulé.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .clean import fold_ar, fold_fr

# ----------------------------------------------------------------- français ---
_FR_TYPES = [
    (r"Loi\s+organique", "loi_organique"),
    (r"Loi", "loi"),
    (r"Ordonnance", "ordonnance"),
    (r"D[ée]cret\s+pr[ée]sidentiel", "decret_presidentiel"),
    (r"D[ée]cret\s+ex[ée]cutif", "decret_executif"),
    (r"D[ée]cret\s+l[ée]gislatif", "decret_legislatif"),
    (r"D[ée]cret", "decret"),
    (r"Arr[êe]t[ée]\s+interminist[ée]riel", "arrete_interministeriel"),
    (r"Arr[êe]t[ée]", "arrete"),
    (r"D[ée]cision", "decision"),
    (r"Circulaire", "circulaire"),
    (r"Instruction", "instruction"),
    (r"D[ée]lib[ée]ration", "deliberation"),
    (r"Proclamation", "proclamation"),
    (r"Avis", "avis"),
]
_FR_TYPE_ALT = "|".join(f"(?P<t{i}>{p})" for i, (p, _) in enumerate(_FR_TYPES))
_NUM = r"(?:\s+n\s*[°ºo]?\s*\.?\s*(?P<num>\d{1,4}\s*[-–]\s*\d{1,4}))?"
FR_HEADING = re.compile(rf"^(?:{_FR_TYPE_ALT}){_NUM}\s+(?:du|des)\s+\S")
FR_PREAMBLE = re.compile(
    r"^(Le\s+Pr[ée]sident\s+de\s+la\s+R[ée]publique|Le\s+Chef\s+du\s+Gouvernement|"
    r"Le\s+Premier\s+ministre|Les?\s+ministres?\b|Le\s+Haut\s+Comit[ée]|L'Assembl[ée]e|"
    r"Le\s+Parlement|Le\s+Conseil|Le\s+wali|Vu\b|Par\s+(d[ée]cret|arr[êe]t[ée]|d[ée]cision)|"
    r"Article\s+1er|Art\.?\s*1er|Sur\s+le\s+rapport|Apr[èe]s\s+avis|"
    r"D[ée]cr[èe]te\s*:|Arr[êe]te\s*:|Promulgue|Ordonne\s*:)",
    re.I,
)
FR_SECTION = re.compile(r"^(MINIST[ÈE]RE|PR[ÉE]SIDENCE|LOIS|ORDONNANCES|D[ÉE]CRETS|ARR[ÊE]T[ÉE]S|"
                        r"CONVENTIONS|AVIS|DECISIONS|D[ÉE]CISIONS|CONSEIL|COUR)\b[^a-z]*$")
_TOC_LINE = re.compile(r"(\.\s*){3,}\s*\d{1,4}\s*$|\.{3,}|…{2,}")
# Ligne de sommaire après OCR (points de conduite perdus) : se termine par un n° de page
# (on exclut les années grégoriennes/hégiriennes et « article 12 », « n° 3 »...)
_TOC_PAGE_END = re.compile(r"[a-zéèêàç.](?<!article)(?<!art\.)\s+"
                           r"(?!(?:13|14|19|20)\d\d\b)\d{1,4}\s*$")
# Mois hégiriens tels qu'écrits au JO (« du 2 / Rajab 1446 ») : seule suite de phrase
# courante qui commence par une majuscule après un retour à la ligne.
_HIJRI_MONTH = re.compile(r"(Mou?harram|Safar|Rabi[ea]|D?joumada|Rad?jab|Cha[âa]bane|"
                          r"Ramadh?an|Chaou[ae]l|Dh?ou)\b", re.I)
_MONTHS_FR = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
              "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12}
_DATE_FR = re.compile(r"(1er|\d{1,2})\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|"
                      r"septembre|octobre|novembre|decembre)\s+(\d{4})")

# ------------------------------------------------------------------- arabe ---
# Motifs écrits sur la forme « pliée » (fold_ar) : sans diacritiques, alifs unifiés.
_AR_TYPES = [
    (r"قانون\s+عضوي", "loi_organique"),
    (r"قانون", "loi"),
    (r"امر", "ordonnance"),
    (r"مرسوم\s+رئاسي", "decret_presidentiel"),
    (r"مرسوم\s+تنفيذي", "decret_executif"),
    (r"مرسوم\s+تشريعي", "decret_legislatif"),
    (r"مرسوم", "decret"),
    (r"قرار\s+وزاري\s+مشترك", "arrete_interministeriel"),
    (r"قرار", "arrete"),
    (r"مقرر", "decision"),
    (r"منشور", "circulaire"),
    (r"تعليمه", "instruction"),
]
_AR_TYPE_ALT = "|".join(f"(?P<t{i}>{p})" for i, (p, _) in enumerate(_AR_TYPES))
AR_HEADING = re.compile(rf"^(?:{_AR_TYPE_ALT})(?:\s+رقم\s*(?P<num>\d{{1,4}}\s*[-–]\s*\d{{1,4}}))?\s+م[ؤو]ر\s?خ\s+في")  # « مؤر خ » : chadda perdue par le PDF, il reste une espace
AR_PREAMBLE = re.compile(r"^(ان\s+رئيس\s+الجمهوريه|ان\s+رئيس\s+الحكومه|ان\s+الوزير|ان\s+وزير|"
                         r"بمقتضي|وبمقتضي|بناء\s+علي|بموجب|المجلس\s+الشعبي|البرلمان|الماده\s+الاولي|"
                         r"يرسم|يقرر|يصدر)")
AR_SECTION = re.compile(r"^(وزاره|رئاسه|قوانين|اوامر|مراسيم|قرارات|مقررات|اراء)\b")
_MONTHS_AR = {"يناير": 1, "جانفي": 1, "فبراير": 2, "فيفري": 2, "مارس": 3, "ابريل": 4, "افريل": 4,
              "مايو": 5, "ماي": 5, "يونيو": 6, "جوان": 6, "يوليو": 7, "جويليه": 7, "غشت": 8,
              "اوت": 8, "اغسطس": 8, "سبتمبر": 9, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12}
_DATE_AR = re.compile(r"(\d{1,2})\s+(" + "|".join(_MONTHS_AR) + r")\s+(?:سنه\s+)?(\d{4})")

LOOKAHEAD = 14  # lignes max entre l'intitulé et le préambule


@dataclass
class Segment:
    seq: int
    text_type: str
    text_number: str | None
    sign_date: str | None
    title: str
    section: str | None
    page_start: int
    page_end: int
    lines: list[str] = field(default_factory=list)

    @property
    def body(self) -> str:
        return "\n".join(self.lines).strip()


def _type_from_match(m, table) -> str:
    for i, (_, code) in enumerate(table):
        if m.group(f"t{i}"):
            return code
    return "inconnu"


def parse_date(title: str, lang: str) -> str | None:
    """Date grégorienne de signature : celle après « correspondant au » si elle existe."""
    if lang == "fr":
        f = fold_fr(title)
        tail = f.split("correspondant au", 1)[1] if "correspondant au" in f else f
        m = _DATE_FR.search(tail)
        if not m:
            return None
        d = 1 if m.group(1) == "1er" else int(m.group(1))
        return f"{int(m.group(3)):04d}-{_MONTHS_FR[m.group(2)]:02d}-{d:02d}"
    f = fold_ar(title)
    tail = f.split("الموافق", 1)[1] if "الموافق" in f else f
    m = _DATE_AR.search(tail)
    if not m:
        return None
    return f"{int(m.group(3)):04d}-{_MONTHS_AR[m.group(2)]:02d}-{int(m.group(1)):02d}"


def canonical_number(raw: str | None, sign_date: str | None) -> str | None:
    """Forme AA-NN telle qu'on la cite (ex. '90-11', '90-02', '97-473') : deux chiffres
    au moins de chaque côté. En arabe l'ordre peut être inversé à l'extraction
    ('11-90') : on remet en tête la partie qui correspond à l'année de signature."""
    if not raw:
        return None
    a, b = [p.strip() for p in re.split(r"[-–]", raw)]
    if sign_date:
        yy = sign_date[2:4]
        if b.zfill(2) == yy and a.zfill(2) != yy:
            a, b = b, a
    return f"{a.zfill(2)}-{str(int(b)).zfill(2)}"


def _continues_sentence(nxt: str | None) -> bool:
    """La ligne suivante prolonge-t-elle la phrase (retour à la ligne dans la colonne) ?
    Oui si elle commence par une minuscule ou par un mois hégirien ; une nouvelle entrée
    de sommaire, un intitulé ou une rubrique commencent par une majuscule."""
    s = (nxt or "").lstrip()
    return bool(s) and (s[0].islower() or bool(_HIJRI_MONTH.match(s)))


def _looks_toc(line: str, nxt: str | None = None) -> bool:
    """Ligne de sommaire ? Points de conduite, ou numéro de page en fin de ligne (OCR).
    Un nombre en fin de ligne n'est un numéro de page que si la phrase s'arrête là :
    « ... correspondant au 2 » suivi de « janvier 2025 ... » est un intitulé coupé."""
    if _TOC_LINE.search(line):
        return True
    return bool(_TOC_PAGE_END.search(line)) and not _continues_sentence(nxt)


def _is_heading(line: str, lang: str, nxt: str | None = None):
    if _looks_toc(line, nxt):
        return None
    if lang == "fr":
        return FR_HEADING.match(line)
    return AR_HEADING.match(fold_ar(line))


def _is_preamble(line: str, lang: str) -> bool:
    return bool(FR_PREAMBLE.match(line) if lang == "fr" else AR_PREAMBLE.match(fold_ar(line)))


def _is_section(line: str, lang: str) -> bool:
    if lang == "fr":
        return bool(FR_SECTION.match(line)) and len(line) < 140
    return bool(AR_SECTION.match(fold_ar(line))) and len(line) < 140


def segment_issue(pages: list[tuple[int, str]], lang: str) -> list[Segment]:
    """pages : [(numéro de page, texte nettoyé)] -> liste ordonnée de Segment."""
    flat: list[tuple[int, str]] = [(p, l) for p, t in pages for l in t.splitlines() if l.strip()]
    segments: list[Segment] = []
    section: str | None = None
    i, cur = 0, None

    def after(k: int) -> str | None:  # ligne qui suit la ligne k (None en fin de numéro)
        return flat[k + 1][1] if k + 1 < len(flat) else None

    while i < len(flat):
        page, line = flat[i]
        m = _is_heading(line, lang, after(i))
        if m:
            # titre = intitulé + lignes suivantes jusqu'au préambule
            j, title_lines, ok = i + 1, [line], False
            while j < len(flat) and j - i <= LOOKAHEAD:
                nxt = flat[j][1]
                if _is_heading(nxt, lang, after(j)) or _looks_toc(nxt, after(j)):
                    break
                if _is_preamble(nxt, lang):
                    ok = True
                    break
                title_lines.append(nxt)
                j += 1
            if ok:
                title = re.sub(r"\s+", " ", " ".join(title_lines)).strip()
                ttype = _type_from_match(m, _FR_TYPES if lang == "fr" else _AR_TYPES)
                date = parse_date(title, lang)
                cur = Segment(
                    seq=len(segments) + 1, text_type=ttype,
                    text_number=canonical_number(m.group("num"), date), sign_date=date,
                    title=title, section=section, page_start=page, page_end=flat[j - 1][0],
                )
                segments.append(cur)
                i = j
                continue
        if _is_section(line, lang):
            section = line.strip()
            i += 1
            continue
        if cur is not None:
            cur.lines.append(line)
            cur.page_end = page
        i += 1
    return segments
