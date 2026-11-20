"""Semaine 1 - Test du LLM seul (sans RAG) sur les questions-test.

Sortie : eval/llm_seul.csv (à annoter à la main : colonnes erreur_type et commentaire)
         docs/preuves/llm_seul.md (lisible dans le rapport)
Les réponses sont en cache (data/llm_cache) : relancer le script ne refait aucun appel.
Usage : python scripts/llm_seul.py
"""
import csv
import time
from pathlib import Path

from jurideazor.config import ROOT, load_config
from jurideazor.llm.client import LLMClient

SYSTEM = ("Tu es un assistant juridique. Réponds à la question sur le droit du travail algérien "
          "en 5 phrases au plus, dans la langue de la question. Cite le texte de loi et le numéro "
          "d'article exacts sur lesquels tu t'appuies.")

cfg = load_config()
llm = LLMClient(cfg)
rows = list(csv.DictReader(open(ROOT / "eval/questions_test.csv", encoding="utf-8")))
out = []
for i, q in enumerate(rows, 1):
    calls_before = llm.stats["api_calls"]
    print(f"[{i}/{len(rows)}] {q['id']} ...", flush=True)
    rep = llm.generate(q["question"], system=SYSTEM)
    out.append({"id": q["id"], "niveau": q["niveau"], "langue": q["langue"], "question": q["question"],
                "reponse_llm_seul": rep.strip(), "erreur_type": "", "commentaire": ""})
    if llm.stats["api_calls"] > calls_before:
        time.sleep(4)  # espacer les appels (limite ~8 000 jetons/minute)

with open(ROOT / "eval/llm_seul.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)

md = [f"# Test du LLM seul (sans RAG) - modèle {llm.model}\n",
      f"Appels réels : {llm.stats['api_calls']} | réponses servies par le cache : {llm.stats['cache_hits']}\n"]
for r in out:
    md += [f"## {r['id']} ({r['niveau']}, {r['langue']})", f"**Question :** {r['question']}\n",
           f"**Réponse :**\n\n{r['reponse_llm_seul']}\n", "**Erreur constatée :** _à remplir_\n"]
(ROOT / "docs/preuves/llm_seul.md").write_text("\n".join(md), encoding="utf-8")
print("OK -> eval/llm_seul.csv et docs/preuves/llm_seul.md")
print(llm.stats)
