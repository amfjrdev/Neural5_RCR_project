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
AR_ART = re.compile(r"^\s*[ء-ي]{1,5}دة\s*(\d{1,3}|الأولى|الاولى)\s*(مكرر)?\s*[:：]")
FR_HEAD = re.compile(r"^\s*(Titre|TITRE|Chapitre|CHAPITRE|Section|SECTION)\b(.*)$")
AR_HEAD = re.compile(r"^\s*(الباب|الفصل|الفرع|القسم)\b(.*)$")
NOISE = re.compile(r"<<<PAGE \d+>>>|JOURNAL OFFICIEL DE LA REPUBLIQUE|الجريدة الرسمية للجمهورية")
LEVEL = {"titre": 0, "الباب": 0, "chapitre": 1, "الفصل": 1, "section": 2, "الفرع": 2, "القسم": 2}


def split(body: str, lang: str):
    art_re, head_re = (FR_ART, FR_HEAD) if lang == "fr" else (AR_ART, AR_HEAD)
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
            # garde-fou : numéro jamais vu et proche du précédent. Évite les renvois (« l'article 22 ci-dessus »)
            # et les chiffres mal lus par l'OCR, tout en acceptant l'ordre perturbé des colonnes (scans AR).
            key = (n, suffix)
            if n is not None and key not in seen and (abs(n - last) <= 6 or (suffix and n == last)):
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
