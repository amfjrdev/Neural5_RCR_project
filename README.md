# Jurideazor

Base de connaissances et assistant de raisonnement sur le **droit du travail algérien** (loi 90-11 et textes associés), construits à partir du Journal officiel (JORADP).
Projet 1 du module RCR, M1 IA, Université Constantine 2.

> Le système **informe**, il ne remplace pas un avocat. Aucun article, numéro ou date absent du corpus ne doit apparaître dans une réponse.

## État : semaine 1, brique « collecte et nettoyage »

```
JORADP (PDF FR/AR) ──► download ──► process ──────────────────────────────► SQLite
  index Upgrowth       robots.txt     extraction (texte natif | OCR)          issues, downloads,
                       pause, SHA-256 nettoyage (en-têtes, césures, accents)  pages, texts
                       rejouable      découpage en textes + métadonnées
                                      filtre « travail » (keep/review/reject)
                                                     │
                                       sample-filter ─► annotation manuelle ─► eval-filter
```

## Installation
```bash
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -e .            # ou : pip install -r requirements.txt
# Tesseract OCR + langues française et arabe
#   Ubuntu : sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-ara
#   Windows : installeur UB-Mannheim, cocher French et Arabic, ajouter au PATH
cp .env.example .env                                  # votre clé personnelle, jamais commitée
cp config/config.example.yaml config/config.yaml      # email d'équipe + modèle annoncé
python -m pytest -q                                   # 8 passed
```
Sans `pip install -e .`, préfixer les commandes par `PYTHONPATH=src`.

## Commandes
| Commande | Rôle |
|---|---|
| `python -m jurideazor check-robots` | Affiche robots.txt des sources (à archiver dans `docs/sources.md`) |
| `python -m jurideazor download [--dry-run] [--no-sample]` | Télécharge les numéros de `config/targets.yaml` ; rejouable sans doublon |
| `python -m jurideazor import-pdf F.pdf --year 1990 --number 17 --edition fr` | Enregistre un PDF obtenu à la main ou du corpus de dépannage |
| `python -m jurideazor process [--no-ocr]` | Extraction, nettoyage, découpage, filtre → table `texts` |
| `python -m jurideazor stats` | État de la base |
| `python -m jurideazor sample-filter --n 20` | Échantillon à annoter → `eval/filter_sample.csv` |
| `python -m jurideazor eval-filter` | Précision / rappel du filtre → `eval/filter_report.md` |
| `python -m jurideazor llm-ping` | Appel de test au modèle commun (avec cache et compteur) |

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
data/          (ignoré par Git) PDF, textes extraits, base, cache LLM
```

## Règles d'usage de l'API (cahier des charges)
Un seul modèle, imposé ; une clé par personne, jamais dans Git ni dans le rapport ; réponses en cache, nombre d'appels reporté ; seulement des textes publics envoyés au modèle ; en cas de panne ou de quota épuisé, prévenir l'enseignant sans changer de modèle.

## Sources et licences
Textes : Journal officiel de la République algérienne (joradp.dz, SGG). Index des numéros : UpGrowth (2026), *Index du Journal officiel algérien*, CC BY 4.0.
