"""Vérifie qu'une installation (clone + README) est dans le même état que celui de l'équipe.

Usage : python scripts/check_setup.py
Chaque ligne affiche OK ou ÉCHEC. Si tout est OK, vous êtes exactement au même point.
Ne fait AUCUN appel au modèle de langage (pas besoin de clé Groq).
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import ast
import csv
import json
import sqlite3
import sys

from jurideazor.config import ROOT, load_config

results = []


def check(name, cond, detail=""):
    results.append(bool(cond))
    print(f"[{'OK' if cond else 'ÉCHEC'}] {name}" + (f" : {detail}" if detail else ""))


check("Python 3.14", sys.version_info[:2] == (3, 14), sys.version.split()[0])
cfg = load_config()
d = cfg["paths"]["data_dir"]

conn = sqlite3.connect(cfg["paths"]["db"])
n_texts = conn.execute("SELECT count(*) FROM texts").fetchone()[0]
n_keep = conn.execute("SELECT count(*) FROM texts WHERE relevance='keep'").fetchone()[0]
n_art = conn.execute("SELECT count(*) FROM article_versions").fetchone()[0]
check("Base SQLite : 410 textes, 37 gardés", (n_texts, n_keep) == (410, 37), f"{n_texts} textes, {n_keep} gardés")
check("Loi 90-11 découpée (157 FR + 135 AR)", n_art == 292, f"{n_art} versions d'articles")

passages = [l for l in open(d / "index" / "passages.jsonl", encoding="utf-8")]
check("Passages indexés : 985", len(passages) == 985, str(len(passages)))

try:
    import faiss
    idx = faiss.read_index(str(d / "index" / "faiss.index"))
    check("Index FAISS lisible (985 vecteurs)", idx.ntotal == 985, str(idx.ntotal))
except Exception as e:  # noqa: BLE001
    check("Index FAISS lisible", False, repr(e))
    idx = None

# Cache du LLM : les 12 réponses du test « LLM seul » doivent être rejouables sans appel
from jurideazor.llm.client import LLMClient
src = open(ROOT / "scripts" / "llm_seul.py", encoding="utf-8").read()
SYSTEM = next(ast.literal_eval(n.value) for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SYSTEM")
llm = LLMClient(cfg)
qs = list(csv.DictReader(open(ROOT / "eval" / "questions_test.csv", encoding="utf-8")))
hits = sum((llm.cache_dir / f"{llm._key(SYSTEM, q['question'])}.json").exists() for q in qs)
check("Cache LLM : 12/12 réponses rejouables sans appel", hits == len(qs) == 12, f"{hits}/{len(qs)}")

# Recherche : la question de référence doit retrouver l'art. 33 (vendredi)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("intfloat/multilingual-e5-small")
q = model.encode(["query: Quel est le jour de repos hebdomadaire ?"], normalize_embeddings=True).astype("float32")
del model
if idx is not None:
    _, I = idx.search(q, 3)
    top = [json.loads(passages[j]) for j in I[0]]
    ok = any(p["text_ref"] == "loi:90-11" and p["article_no"] == "33" for p in top)
    check("Recherche « jour de repos » -> loi 90-11 art. 33 dans le top 3", ok,
          ", ".join(f"{p['text_ref']} art.{p['article_no']}" for p in top))

print()
print("TOUT EST OK : vous êtes au même point que l'équipe." if all(results)
      else "Au moins une vérification a échoué : envoyez cette sortie à l'équipe.")
