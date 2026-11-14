"""Traitement d'un numéro téléchargé : extraction -> nettoyage -> découpage -> filtre -> base.

Rejouable : les textes d'un numéro sont reconstruits dans une transaction
(suppression puis réinsertion), donc relancer ne crée jamais de doublons.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .db import NORM_RANK
from .extract.clean import clean_page
from .extract.pdf_text import extract_pages
from .extract.segment import segment_issue
from .filter.labor import classify


def process_issue(conn, cfg: dict, issue_id: int, allow_ocr: bool = True) -> dict:
    row = conn.execute(
        """SELECT i.*, d.local_path FROM issues i JOIN downloads d ON d.issue_id = i.id
           WHERE i.id = ? AND d.error IS NULL""", (issue_id,)).fetchone()
    if row is None:
        raise ValueError(f"issue {issue_id} non téléchargée")
    lang = row["edition"]
    ex = cfg["extract"]
    pages = extract_pages(row["local_path"], lang, ex["ocr_min_chars_per_page"], ex["ocr_dpi"], allow_ocr)

    # Sauvegarde du texte brut nettoyé (utile pour déboguer le découpage)
    cleaned = [(p.page_no, clean_page(p.text, lang)) for p in pages]
    txt_dir: Path = cfg["paths"]["data_dir"] / "text" / lang / str(row["year"])
    txt_dir.mkdir(parents=True, exist_ok=True)
    (txt_dir / f"{Path(row['local_path']).stem}.txt").write_text(
        "\n".join(f"\n<<<PAGE {n}>>>\n{t}" for n, t in cleaned), encoding="utf-8")

    segs = segment_issue(cleaned, lang)
    methods = {p.page_no: p.method for p in pages}
    f = cfg["filter"]
    with conn:  # transaction
        conn.execute("DELETE FROM pages WHERE issue_id=?", (issue_id,))
        conn.executemany("INSERT INTO pages (issue_id, page_no, method, chars) VALUES (?,?,?,?)",
                         [(issue_id, p.page_no, p.method, len(p.text)) for p in pages])
        # on garde les annotations manuelles existantes (par empreinte du contenu)
        gold = {r["content_sha256"]: r["gold_label"] for r in conn.execute(
            "SELECT content_sha256, gold_label FROM texts WHERE issue_id=? AND gold_label IS NOT NULL",
            (issue_id,))}
        conn.execute("DELETE FROM texts WHERE issue_id=?", (issue_id,))
        for s in segs:
            body = s.body
            digest = hashlib.sha256((s.title + "\n" + body).encode("utf-8")).hexdigest()
            used = {methods.get(p) for p in range(s.page_start, s.page_end + 1)}
            method = "mixed" if len(used) > 1 else (used.pop() if used else None)
            d = classify(s.title, body, s.section, s.text_type, lang,
                         f["keep_threshold"], f["review_threshold"])
            conn.execute(
                """INSERT INTO texts (issue_id, seq, lang, text_type, text_number, sign_date, norm_rank,
                     title, section, page_start, page_end, body, content_sha256, extraction_method,
                     relevance, relevance_score, relevance_reasons, is_circular, gold_label, source_url)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (issue_id, s.seq, lang, s.text_type, s.text_number, s.sign_date,
                 NORM_RANK.get(s.text_type), s.title, s.section, s.page_start, s.page_end, body,
                 digest, method, d.relevance, d.score, json.dumps(d.reasons, ensure_ascii=False),
                 int(d.is_circular), gold.get(digest), row["url"]),
            )
    counts = {"pages": len(pages), "ocr_pages": sum(p.method == "ocr" for p in pages), "texts": len(segs)}
    for rel in ("keep", "review", "reject"):
        counts[rel] = conn.execute("SELECT COUNT(*) FROM texts WHERE issue_id=? AND relevance=?",
                                   (issue_id, rel)).fetchone()[0]
    return counts
