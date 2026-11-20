# Jurideazor

Base de connaissances et assistant de raisonnement sur le **droit du travail algérien** (loi 90-11 et textes associés), construits à partir du Journal officiel (JORADP).
Projet 1 du module RCR, M1 IA, Université Constantine 2.

> Le système **informe**, il ne remplace pas un avocat. Aucun article, numéro ou date absent du corpus ne doit apparaître dans une réponse.

## État du projet (fin de semaine 2)

```
JORADP (PDF FR/AR) → download → process (texte natif | OCR) → textes + métadonnées → filtre « travail »
   → split_articles (loi 90-11 article par article) → build_index (passages + E5 + FAISS) → search
```

| Brique | État | Preuve |
|---|---|---|
| Collecte rejouable (18 PDF FR+AR, 0 doublon) | ✅ | `docs/preuves/download_*.txt` |
| Extraction / OCR (620 pages, 379 en OCR, 410 textes) | ✅ | `docs/preuves/process_2.txt` |
| Filtre « travail » (20 textes annotés : P 0,60, R 1,00) | ✅ | `eval/filter_report.md` |
| Test du LLM seul (12 questions, 12/12 avec erreurs) | ✅ | `docs/preuves/llm_seul.md` |
| Vérification sur PDF (divergence FR/AR art. 18) | ✅ | `docs/preuves/verification_pdf.md` |
| Loi 90-11 en articles (FR 157/158, AR 135/158) | ✅ | `docs/preuves/articles_90-11.md` |
| BM25 vs E5 (R@3, R@5, MRR, inter-langues) | ✅ | `docs/preuves/retrieval_s02.md` |
| Base vectorielle FAISS (985 passages) | ✅ | `docs/preuves/index_s02.md` |
| Versions datées / relations « modifie » (brique 3) | ⏳ S3 | |

**Bugs connus** : OCR arabe (23 articles AR manquants, dont l'art. 12) ; ordre des chiffres AR
(« 21-96 » au lieu de 96-21) ; titre/corps décalés pour le décret législatif 94-03 ; 91-29, 97-02, 97-03
non retenus en AR ; « CDD » ne retrouve pas l'art. 12 (abréviation).

## Démarrage rapide (la base est déjà dans Git)
Les données dérivées sont versionnées (`data/jurideazor.sqlite`, `data/articles/`, `data/index/`,
`data/text/`, `data/llm_cache/`). Seuls les PDF (`data/raw/`) ne le sont pas.
```bash
git pull
python3 -m venv .venv && source .venv/bin/activate     # macOS : python3 ; Windows : .venv\Scripts\activate
pip install -e . && pip install -r requirements.txt
cp .env.example .env                                   # mettre VOTRE clé Groq (une par personne)
cp config/config.example.yaml config/config.yaml
python scripts/search.py "Quel est le jour de repos hebdomadaire ?"   # 1er lancement : télécharge E5 (~470 Mo)
python scripts/eval_retrieval.py                                       # rejoue la comparaison BM25 / E5
python scripts/llm_seul.py                                             # rejoue le test LLM depuis le cache (0 appel)
```

## Tout reconstruire depuis zéro (~1 h, surtout l'OCR)
Prérequis : Tesseract avec `fra` et `ara` (macOS : `brew install tesseract tesseract-lang`).
| Ordre | Commande | Durée | Produit |
|---|---|---|---|
| 1 | `python -m jurideazor download` | ~3 min | `data/raw/` (18 PDF) |
| 2 | `python -m jurideazor process` | 30-60 min | base SQLite, `data/text/` |
| 3 | `python scripts/split_articles.py` | secondes | `data/articles/90-11.jsonl` |
| 4 | `python scripts/build_index.py` | ~1 min | `data/index/` (FAISS) |
| 5 | `python scripts/eval_retrieval.py` | ~1 min | `docs/preuves/retrieval_s02.md` |

## Scripts (semaines 1-2)
| Script | Rôle |
|---|---|
| `scripts/llm_seul.py` | Test du LLM seul (sans RAG) sur `eval/questions_test.csv`, avec cache |
| `scripts/split_articles.py` | Découpage d'une loi en articles → tables `articles` / `article_versions` |
| `scripts/eval_retrieval.py` | Comparaison BM25 vs embeddings E5 (dont test inter-langues FR↔AR) |
| `scripts/build_index.py` | Passages de tous les textes gardés + embeddings + index FAISS |
| `scripts/search.py "question"` | Recherche dans l'index, avec référence et lien source |

## Prochaines tâches (S3), une par personne, chacune avec son commit
1. Découper en articles les textes modificatifs (91-29, 94-03, 96-21, 97-02, 97-03).
2. Table `relations` : « modifie / complète / abroge » (texte, article, date) → versions datées de la 90-11.
3. Corriger l'ordre des chiffres arabes (« 21-96 ») et le décalage titre/corps (94-03) dans `extract/segment.py`, avec un test pour chaque cas.
4. Ajouter au moins 18 questions (objectif 30, dont 10 en arabe) avec l'article attendu lu dans le texte officiel.
5. Recherche : expansion des abréviations (CDD, CDI) et recherche hybride BM25 + E5, avec mesures avant / après.
6. Ontologie minimale (texte, article, version, modifie / abroge / applique) et graphe (`networkx`).

## Commandes de base
| Commande | Rôle |
|---|---|
| `python -m jurideazor check-robots` | Affiche robots.txt des sources |
| `python -m jurideazor download [--dry-run]` | Télécharge les numéros de `config/targets.yaml` ; rejouable sans doublon |
| `python -m jurideazor import-pdf F.pdf --year 1990 --number 17 --edition fr` | Enregistre un PDF obtenu à la main |
| `python -m jurideazor process [--no-ocr]` | Extraction, nettoyage, découpage, filtre → table `texts` |
| `python -m jurideazor stats` | État de la base |
| `python -m jurideazor sample-filter --n 20` / `eval-filter` | Évaluation du filtre |
| `python -m jurideazor llm-ping` | Appel de test au modèle commun |

## Organisation
```
config/        config.example.yaml, targets.yaml (numéros du JO visés)
docs/          PLAN_SEMAINE_01.md, sources.md, RAPPORT_HEBDO_S01.md
eval/          questions_test.csv, filter_sample.csv, filter_report.md
src/jurideazor/
  collect/     index.py (index Upgrowth), download.py (robots, pause, SHA-256)
  extract/     pdf_text.py (colonnes, OCR), clean.py, segment.py (textes + métadonnées)
  filter/      labor.py (règles + score, FR/AR)
  llm/         client.py (modèle commun, cache disque, compteur d'appels)
  db.py        schéma SQLite (y compris articles / versions / relations à venir)
  pipeline.py, evaluate.py, cli.py
tests/         make_fixtures.py (faux JO texte + scanné), test_week1.py
scripts/       scripts des semaines 1-2 (voir tableau ci-dessus)
data/          base SQLite, textes, articles, index FAISS, cache LLM (versionnés) ; raw/ = PDF (non versionnés)
```

## Règles d'usage de l'API (cahier des charges)
Un seul modèle, imposé ; une clé par personne, jamais dans Git ni dans le rapport ; réponses en cache, nombre d'appels reporté ; seulement des textes publics envoyés au modèle ; en cas de panne ou de quota épuisé, prévenir l'enseignant sans changer de modèle.

## Sources et licences
Textes : Journal officiel de la République algérienne (joradp.dz, SGG). Index des numéros : UpGrowth (2026), *Index du Journal officiel algérien*, CC BY 4.0.
