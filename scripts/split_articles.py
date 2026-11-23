"""Semaine 2 - Découpage article par article (brique 2 du cahier des charges).

Lit le texte isolé d'une loi (table texts) en FR et en AR, le découpe en articles,
garde la hiérarchie (Titre > Chapitre > Section) et remplit les tables
articles / article_versions. Écrit aussi data/articles/<loi>.jsonl (pour la recherche)
et docs/preuves/articles_<loi>.md (contrôle : nombre d'articles, numéros manquants).

Usage : python scripts/split_articles.py            (loi 90-11 par défaut)
        python scripts/split_articles.py --loi 90-02
"""
import argparse
import json
import re
import sqlite3

from jurideazor.config import ROOT, load_config

AR_ORD = {"الأولى": 1, "الاولى": 1, "الأول": 1, "الاول": 1}
# tolérant aux défauts d'OCR : « Ârt. 30. — », « Art 48. — », « Art. 82: », « . Art. 96. — », « Art. 155..-— »
FR_ART = re.compile(r"^\W{0,3}[AÂÃÀÄ]rt(?:icle|\.)?\s*(\d{1,3})\s*(er|bis|ter)?\s*[.,:]*\s*[-—–+:]", re.I)
AR_ART = re.compile(r"^\W{0,3}[ء-ي]{1,5}د[ةه]?\s*(\d{1,3}|الأولى|الاولى)\s*(مكرر)?\s*[:：.\-—]")
FR_HEAD = re.compile(r"^\s*(Titre|TITRE|Chapitre|CHAPITRE|Section|SECTION)\b(.*)$")
AR_HEAD = re.compile(r"^\s*(الباب|الفصل|الفرع|القسم)\b(.*)$")
NOISE = re.compile(r"<<<PAGE \d+>>>|JOURNAL OFFICIEL DE LA REPUBLIQUE|الجريدة الرسمية للجمهورية")
LEVEL = {"titre": 0, "الباب": 0, "chapitre": 1, "الفصل": 1, "section": 2, "الفرع": 2, "القسم": 2}

def clean_arabic_ocr_text(text: str) -> str:
    # 1. تحويل الأرقام الهندية (٠-٩) إلى أرقام عادية (0-9)
    arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    text = text.translate(arabic_digits)

    # 2. تصحيح أخطاء كتابة كلمة "المادة" (تاء مربوطة ممسوحة أو مسافة داخل الكلمة)
    text = re.sub(r"(?:ا\s*ل\s*م\s*ا\s*د\s*[ةه]?|الملدة|الماد|المادةّ|الماذة)\s*[:：.\-—]?\s*(?=\d)", "المادة ", text)

    # 3. دمج الأرقام المفصولة بمسافة مثل "المادة 3 5 :" أو "المادة 1 0 0 :"
    text = re.sub(r"(المادة\s+)(\d)\s+(\d)\s+(\d)\b", r"\1\2\3\4", text)
    text = re.sub(r"(المادة\s+)(\d{1,2})\s+(\d{1,2})\b", r"\1\2\3", text)

    # 4. تصحيح المادة 65 المشوهة ("3 5" في سياق المادة 64/66)
    text = re.sub(
        r"(المادة\s+64\b.*?)(المادة\s+)35(\s*[:：.\-—])",
        r"\g<1>\g<2>65\3",
        text,
        flags=re.S,
    )

    # 5. فرض سطر جديد قبل أي "المادة <رقم>" تظهر في منتصف السطر
    text = re.sub(r"([^\n])\s+(المادة\s+\d+)", r"\1\n\2", text)

    return text

def split(body: str, lang: str):
    art_re, head_re = (FR_ART, FR_HEAD) if lang == "fr" else (AR_ART, AR_HEAD)
    if lang == "ar":
        body = clean_arabic_ocr_text(body)
        body = re.sub(r"(?<!^)\s+([ء-ي]{1,5}د[ةه]?\s*(?:\d{1,3}|الأولى|الاولى)\s*(?:مكرر)?\s*[:：.\-—])", r"\n\1", body)
    path = ["", "", ""]
    arts, cur, last = [], None, 0
    seen = set()
    for line in body.splitlines():
        line = line.replace("\u200f", "").replace("\u200e", "")
        if NOISE.search(line):
            continue
        h = head_re.match(line)
        if h and len(line) < 80:
            lvl = LEVEL[h.group(1).lower()] if lang == "fr" else LEVEL[h.group(1)]
            path[lvl] = line.strip()
            for k in range(lvl + 1, 3):
                path[k] = ""
            continue
        m = art_re.match(line)
        if m:
            raw = m.group(1)
            n = AR_ORD.get(raw, None) if not raw.isdigit() else int(raw)
            suffix = m.group(2) or ""
            key = (n, suffix)
            valid_jump = (1 <= n <= 200) if lang == "ar" else (abs(n - last) <= 6 or (suffix and n == last))
            if n is not None and key not in seen and valid_jump:
                seen.add(key)
                if cur:
                    arts.append(cur)
                no = str(n) + (" bis" if suffix in ("bis", "مكرر") else "")
                cur = {"article_no": no, "n": n, "parent_path": " > ".join(p for p in path if p),
                       "lines": [line.strip()]}
                last = n
                continue
        if cur is not None:
            cur["lines"].append(line.strip())
    if cur:
        arts.append(cur)
    arts.sort(key=lambda a: (a["n"], a["article_no"]))
    for a in arts:
        a["content"] = re.sub(r"\s+", " ", " ".join(a.pop("lines"))).strip()
    return arts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loi", default="90-11")
    a = ap.parse_args()
    cfg = load_config()
    conn = sqlite3.connect(cfg["paths"]["db"])
    conn.execute("PRAGMA foreign_keys = ON")
    text_ref = f"loi:{a.loi}"
    out_dir = cfg["paths"]["data_dir"] / "articles"
    out_dir.mkdir(exist_ok=True)
    jsonl = open(out_dir / f"{a.loi}.jsonl", "w", encoding="utf-8")
    report = [f"# Découpage en articles : loi {a.loi}\n", "| Langue | Articles trouvés | Dernier n° | Numéros manquants |", "|---|---|---|---|"]
    for lang in ("fr", "ar"):
        row = conn.execute("""SELECT t.id, t.body, t.sign_date, t.source_url FROM texts t
                              WHERE t.text_number=? AND t.lang=? AND t.text_type='loi'
                              ORDER BY length(t.body) DESC LIMIT 1""", (a.loi, lang)).fetchone()
        if not row:
            report.append(f"| {lang} | texte absent de la base | | |")
            continue
        tid, body, date, url = row
        arts = split(body, lang)
        nums = [x["n"] for x in arts]
        missing = sorted(set(range(1, max(nums) + 1)) - set(nums)) if nums else []
        report.append(f"| {lang} | {len(arts)} | {max(nums) if nums else '-'} | {', '.join(map(str, missing)) or 'aucun'} |")
        for x in arts:
            conn.execute("INSERT OR IGNORE INTO articles(text_ref, article_no, parent_path) VALUES (?,?,?)",
                         (text_ref, x["article_no"], x["parent_path"] if lang == "fr" else None))
            if lang == "fr":
                conn.execute("UPDATE articles SET parent_path=? WHERE text_ref=? AND article_no=?",
                             (x["parent_path"], text_ref, x["article_no"]))
            art_id = conn.execute("SELECT id FROM articles WHERE text_ref=? AND article_no=?",
                                  (text_ref, x["article_no"])).fetchone()[0]
            # Version initiale (JO d'origine). Les versions modifiées seront ajoutées avec les textes modificatifs.
            conn.execute("""INSERT INTO article_versions(article_id, lang, content, valid_from, valid_to, status, source_text_id)
                            VALUES (?,?,?,?,NULL,'en_vigueur',?)
                            ON CONFLICT(article_id, lang, valid_from) DO UPDATE SET content=excluded.content,
                            source_text_id=excluded.source_text_id""",
                         (art_id, lang, x["content"], date, tid))
            jsonl.write(json.dumps({"id": f"{a.loi}:{lang}:{x['article_no']}", "loi": a.loi, "lang": lang,
                                    "article_no": x["article_no"], "parent_path": x["parent_path"],
                                    "valid_from": date, "source_url": url, "content": x["content"]},
                                   ensure_ascii=False) + "\n")
    conn.commit()
    jsonl.close()
    report += ["", "Version enregistrée : version initiale (JO d'origine), valid_from = date de la loi.",
               "Les versions modifiées (91-29, 96-21, 97-02...) seront ajoutées à partir des textes modificatifs (brique 3)."]
    (ROOT / "docs/preuves" / f"articles_{a.loi}.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()