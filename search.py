"""Recherche dans la base vectorielle : python scripts/search.py "ma question" [-k 5]

Affiche les passages les plus proches avec leur référence (texte, article, langue, lien source).
Les circulaires sont signalées comme « interprétation de l'administration ».
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import argparse
import json

import numpy as np

from jurideazor.config import load_config

ap = argparse.ArgumentParser()
ap.add_argument("question")
ap.add_argument("-k", type=int, default=5)
ap.add_argument("--model", default="intfloat/multilingual-e5-small")
a = ap.parse_args()
cfg = load_config()
d = cfg["paths"]["data_dir"] / "index"
passages = [json.loads(l) for l in open(d / "passages.jsonl", encoding="utf-8")]
from sentence_transformers import SentenceTransformer
q = SentenceTransformer(a.model).encode(["query: " + a.question], normalize_embeddings=True).astype("float32")
try:
    import faiss
    S, I = faiss.read_index(str(d / "faiss.index")).search(q, a.k)
    S, I = S[0], I[0]
except ImportError:
    D = np.load(d / f"{a.model.split('/')[-1]}.npy")
    s = (q @ D.T)[0]
    I = np.argsort(-s)[:a.k]
    S = s[I]
for rank, (score, j) in enumerate(zip(S, I), 1):
    p = passages[j]
    tag = " [circulaire : interprétation de l'administration]" if p.get("circulaire") else ""
    print(f"\n{rank}. {p['text_ref']} art. {p['article_no'] or '-'} ({p['lang']}, {p['date']}) score={score:.3f}{tag}")
    print(f"   {p['content'][:300]}")
    print(f"   source : {p['source_url']}")
