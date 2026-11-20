"""Semaine 2 - Comparaison BM25 (mots-clés) vs embeddings multilingues (E5) sur les articles.

Corpus : data/articles/*.jsonl (produit par split_articles.py), FR + AR.
Questions : eval/questions_test.csv (colonne article_attendu ; hors périmètre exclu).
Mesures : Recall@3, Recall@5, MRR@10, par langue de question, et test inter-langues
          (question FR sur index AR seul, question AR sur index FR seul).
Sorties : docs/preuves/retrieval_s02.md, eval/retrieval_details.csv
Les vecteurs sont enregistrés dans data/embeddings/ (pas recalculés à chaque fois).

Usage : python scripts/eval_retrieval.py [--model intfloat/multilingual-e5-small]
"""
import argparse
import csv
import json
import re
import unicodedata

import numpy as np
from rank_bm25 import BM25Okapi

from jurideazor.config import ROOT, load_config

AR_NORM = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي", "ـ": ""})
STOP = set("le la les de des du un une et en à a au aux pour par sur dans est sont il elle qui que quel quelle quels quelles "
           "ce cette ces se sa son ses ou ne pas peut être l d qu n s y on avec".split()) | set(
           "في من على الى إلى عن ما هو هي هل التي الذي ان أن او أو لا مع".split())


def tok(s: str):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c)).translate(AR_NORM)
    return [w for w in re.findall(r"\w+", s) if w not in STOP and len(w) > 1]


def expected(cell: str):
    return {int(m) for m in re.findall(r"(?<![\d-])(\d{1,3})(?![\d])", cell.split("(")[0] if "version" in cell else cell)}


def base(no: str):
    return int(re.match(r"\d+", no).group())


def metrics(ranked_lists, gold_sets):
    r3 = r5 = mrr = 0.0
    for ranked, gold in zip(ranked_lists, gold_sets):
        bases = [base(x) for x in ranked]
        r3 += any(b in gold for b in bases[:3])
        r5 += any(b in gold for b in bases[:5])
        for i, b in enumerate(bases[:10]):
            if b in gold:
                mrr += 1 / (i + 1)
                break
    n = max(len(gold_sets), 1)
    return r3 / n, r5 / n, mrr / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    a = ap.parse_args()
    cfg = load_config()
    docs = []
    for f in sorted((cfg["paths"]["data_dir"] / "articles").glob("*.jsonl")):
        docs += [json.loads(l) for l in open(f, encoding="utf-8")]
    qs = [q for q in csv.DictReader(open(ROOT / "eval/questions_test.csv", encoding="utf-8"))
          if q["hors_perimetre"] != "oui" and q["article_attendu"].strip()]
    gold = [expected(q["article_attendu"]) for q in qs]
    print(f"{len(docs)} articles indexés, {len(qs)} questions évaluées")

    # --- BM25
    bm25 = BM25Okapi([tok(d["content"]) for d in docs])
    bm_scores = np.array([bm25.get_scores(tok(q["question"])) for q in qs])

    # --- Embeddings E5 (préfixes obligatoires query: / passage:)
    from sentence_transformers import SentenceTransformer
    emb_dir = cfg["paths"]["data_dir"] / "embeddings"
    emb_dir.mkdir(exist_ok=True)
    tag = a.model.split("/")[-1]
    cache = emb_dir / f"{tag}_{len(docs)}.npy"
    model = SentenceTransformer(a.model)
    if cache.exists():
        D = np.load(cache)
    else:
        D = model.encode(["passage: " + d["content"][:2000] for d in docs], normalize_embeddings=True,
                         batch_size=16, show_progress_bar=True)
        np.save(cache, D)
    Q = model.encode(["query: " + q["question"] for q in qs], normalize_embeddings=True)
    em_scores = Q @ D.T

    def ranked(scores, mask=None):
        out = []
        for i in range(len(qs)):
            s = scores[i].copy()
            if mask is not None:
                s[~mask(qs[i])] = -1e9
            out.append([f"{docs[j]['article_no']}|{docs[j]['lang']}" for j in np.argsort(-s)[:10]])
        return out

    def run(scores, sel=None, mask=None):
        R = ranked(scores, mask)
        idx = [i for i in range(len(qs)) if sel is None or sel(qs[i])]
        return metrics([[x.split("|")[0] for x in R[i]] for i in idx], [gold[i] for i in idx]), R

    langs = np.array([d["lang"] for d in docs])
    other = lambda q: (lambda: None)
    rows = []
    settings = [
        ("Toutes questions, index FR+AR", None, None),
        ("Questions FR, index FR+AR", lambda q: q["langue"] == "fr", None),
        ("Questions AR, index FR+AR", lambda q: q["langue"] == "ar", None),
        ("Inter-langues : question FR -> articles AR seuls", lambda q: q["langue"] == "fr", "ar"),
        ("Inter-langues : question AR -> articles FR seuls", lambda q: q["langue"] == "ar", "fr"),
    ]
    details = {}
    for name, sel, only in settings:
        mask = None
        if only:
            mask_arr = langs == only
            mask = lambda q, m=mask_arr: m
        (b3, b5, bm), Rb = run(bm_scores, sel, mask)
        (e3, e5, em), Re = run(em_scores, sel, mask)
        n = sum(1 for q in qs if sel is None or sel(q))
        rows.append(f"| {name} | {n} | {b3:.2f} | {b5:.2f} | {bm:.2f} | {e3:.2f} | {e5:.2f} | {em:.2f} |")
        if name.startswith("Toutes"):
            details = (Rb, Re)

    md = [f"# Recherche : BM25 vs embeddings ({a.model})\n",
          f"Corpus : {len(docs)} articles (loi 90-11, FR + AR, version initiale). Questions : {len(qs)} (hors périmètre exclu).",
          "Une question est réussie si un article attendu (numéro de base) est dans les k premiers résultats.\n",
          "| Cas | n | BM25 R@3 | BM25 R@5 | BM25 MRR | E5 R@3 | E5 R@5 | E5 MRR |",
          "|---|---|---|---|---|---|---|---|"] + rows
    (ROOT / "docs/preuves/retrieval_s02.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with open(ROOT / "eval/retrieval_details.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "langue", "question", "article_attendu", "bm25_top5", "e5_top5"])
        for i, q in enumerate(qs):
            w.writerow([q["id"], q["langue"], q["question"], q["article_attendu"],
                        " ; ".join(details[0][i][:5]), " ; ".join(details[1][i][:5])])
    print("\n".join(md))


if __name__ == "__main__":
    main()
