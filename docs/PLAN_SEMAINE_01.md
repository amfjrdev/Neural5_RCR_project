# Jurideazor — Semaine 1 : cadrage et brique 1 (collecte et nettoyage)

> **Objectif de la semaine** : à la fin de la semaine, l'équipe sait **rejouer d'une commande** la collecte d'une dizaine de numéros du Journal officiel (FR + AR), chaque numéro est **découpé en textes** avec leurs métadonnées et leur lien source, les textes qui ne concernent pas le travail sont **écartés**, et la qualité de ce filtre est **mesurée** sur 20 textes annotés à la main.

Fonctionnalité visée dans le cahier des charges : **n°1 « Collecter et nettoyer les textes »**. Critères de réussite repris tels quels :
- la collecte peut être rejouée **sans doublons** ;
- chaque texte garde un **lien vers sa source** ;
- la qualité du filtrage est **mesurée** sur un échantillon vérifié à la main (20 textes).

---

## 1. À confirmer auprès de l'enseignant (en début de semaine)

| Question | Pourquoi | Où l'inscrire |
|---|---|---|
| Nom **exact** du modèle commun et fournisseur. Le cahier des charges parle de **Gemini (Google AI Studio)** ; les consignes « Usage de l'IA / Embeddings » mentionnent **Groq**. | Un seul modèle est autorisé dans le système rendu. | `config/config.yaml` → `llm.provider`, `llm.model` |
| Accès au **corpus de dépannage** si joradp.dz bloque les téléchargements. | Plan B. La collecte doit quand même être démontrée sur quelques numéros. | `python -m jurideazor import-pdf ... --origin corpus_depannage` |
| Format exact du **rapport d'avancement hebdomadaire**. | Le champ « outils d'IA utilisés » y est prévu. | `docs/RAPPORT_HEBDO_S01.md` |

---

## 2. Répartition des rôles (équipe de 5 ; à 4, R4 et R5 fusionnent)

| Rôle | Responsable de | Livrable semaine 1 |
|---|---|---|
| **R1 Intégration** | Dépôt Git, conventions, revue des PR, `config/`, `.gitignore`, base SQLite | Dépôt propre, tous les membres committent, `pytest` vert |
| **R2 Collecte** | Conditions d'utilisation, robots.txt, index Upgrowth, téléchargement poli | `docs/sources.md` complété, 12+ PDF téléchargés, preuve du rejeu |
| **R3 Extraction / OCR** | Texte natif vs scan, OCR fra/ara, nettoyage (en-têtes, césures, accents) | Taux de pages OCR, contrôle qualité OCR sur 1 page de la loi 90-11 |
| **R4 Découpage** | Repérage des intitulés, métadonnées (type, n°, date), sommaire ignoré | Textes du numéro 17/1990 correctement isolés (FR et AR) |
| **R5 Filtre & évaluation** | Règles du filtre, échantillon annoté, précision / rappel, début du jeu de test | `eval/filter_report.md`, 10 premières questions-test |

Tout le monde : créer **sa propre clé** API (une par personne, jamais dans Git), lire l'avant-propos juridique du cahier des charges.

---

## 3. Tâches détaillées

### Jour 1 — Cadrage et socle
- [ ] **R1** Créer le dépôt Git partagé, y pousser ce squelette, protéger `main` (PR + 1 relecture).
- [ ] **Tous** `pip install -r requirements.txt` ; installer Tesseract + langues `fra` et `ara` ; `python -m pytest -q` doit afficher **13 passed**.
- [ ] **Tous** copier `.env.example` → `.env` et `config/config.example.yaml` → `config/config.yaml` ; mettre l'email d'équipe dans `user_agent`.
- [ ] **R1** Relire le schéma `src/jurideazor/db.py` en équipe : il fixe dès maintenant les tables des semaines suivantes (`articles`, `article_versions`, `relations`). Le modifier maintenant coûte moins cher que plus tard.

### Jour 2 — Sources et règles d'accès (R2)
- [ ] Lire les conditions d'utilisation de joradp.dz ; lancer `python -m jurideazor check-robots` et **coller la sortie datée** dans `docs/sources.md`.
- [ ] Vérifier la licence de l'index Upgrowth (CC BY 4.0 : citer la source dans le rapport).
- [ ] **Ne pas** aspirer le recueil du ministère du Commerce (interdit par son robots.txt).
- [ ] Vérifier dans l'index Upgrowth les numéros listés dans `config/targets.yaml`, trouver celui de la **loi 22-16** (2022), passer `verifie: true` après contrôle du sommaire.

### Jours 2-3 — Collecte (R2) et extraction (R3)
- [ ] `python -m jurideazor download --dry-run` puis `download` (pause de 5 s entre requêtes, crawl-delay respecté).
- [ ] **Preuve du rejeu** : relancer `download` → tout doit sortir en `skipped`, et `stats` ne doit montrer aucun doublon. Capture d'écran pour le rapport.
- [ ] `python -m jurideazor process` ; ouvrir les fichiers `data/text/...txt` et noter les défauts (ordre des colonnes, en-têtes oubliés, caractères arabes mal ordonnés).
- [ ] **R3 contrôle OCR** : prendre 1 page de la loi 90-11 (scan 1990), comparer l'OCR au texte de WIPO Lex (version 1997, donc choisir des articles non modifiés) et calculer un taux d'erreur par caractère. Une ligne dans le rapport.
- [ ] **R3** édition arabe : vérifier que le texte extrait se lit dans le bon ordre (PDF natifs récents). Si l'ordre est inversé, le signaler : c'est le risque n°1 pour le test arabe obligatoire.

### Jours 3-4 — Découpage (R4) et filtre (R5)
- [ ] **R4** Sur le n°17/1990 : la loi 90-11 doit sortir comme **un seul texte** `loi 90-11`, date `1990-04-21`. Lister les intitulés ratés ou en trop, ajuster les motifs dans `extract/segment.py`, ajouter un test pour chaque cas corrigé.
- [ ] **R5** `python -m jurideazor sample-filter --n 20` → remplir `gold` (keep / reject) **sans regarder `predicted`** ; deux annotateurs sur les cas douteux.
- [ ] **R5** `python -m jurideazor eval-filter` → `eval/filter_report.md` (précision, rappel, F1, liste des erreurs). Analyser chaque erreur : règle à ajouter ou cas limite à documenter.
- [ ] **R5** Démarrer `eval/questions_test.csv` (voir § 5).

### Jour 5 — Intégration et rapport
- [ ] **R1** Fusion des branches, `pytest` vert, tag `s01`.
- [ ] **Tous** `python -m jurideazor llm-ping` (une seule fois par personne : vérifie clé + cache + compteur d'appels).
- [ ] Rapport hebdomadaire `docs/RAPPORT_HEBDO_S01.md` (chiffres + outils d'IA utilisés).

---

## 4. Définition de « terminé » (à vérifier ensemble vendredi)

| Critère | Mesure | Cible S1 |
|---|---|---|
| Collecte rejouable | 2ᵉ passage de `download` = 100 % `skipped`, 0 doublon dans `issues` | ✔ |
| Provenance | % de textes avec `source_url` | 100 % |
| Couverture | numéros téléchargés (FR + AR) | ≥ 12 PDF |
| Extraction | % de pages OCR, taux d'erreur OCR sur 1 page | chiffres notés |
| Découpage | loi 90-11 isolée en FR et en AR avec bon n° et bonne date | ✔ |
| Filtre | précision / rappel sur 20 textes annotés | chiffrés ; viser rappel ≥ 0,9 |
| Jeu de test | questions rédigées | ≥ 10, dont ≥ 5 en arabe |
| Hygiène | aucune clé dans Git, `pytest` vert | ✔ |

Pourquoi le **rappel** compte plus que la précision : un texte du travail écarté à tort n'existera jamais pour l'assistant, alors qu'un texte gardé à tort sera simplement peu retrouvé par la recherche.

---

## 5. Jeu de test : commencer dès maintenant

Le jeu final demande **≥ 30 questions** avec la réponse attendue et l'article de référence, et la consigne « Embeddings » impose **≥ 5 questions dont la réponse est dans un texte arabe**. Commencer en S1 permet d'orienter la collecte. Le fichier `eval/questions_test.csv` contient les 7 exemples du cahier des charges et 5 questions en arabe. Les colonnes `article_attendu` et `reponse_attendue` sont à remplir **en lisant le texte officiel**, jamais de mémoire ni à partir d'un chatbot.

---

## 6. Lien avec le cours

- **Chapitre 01 (RCR à l'ère de l'IA générative)** : un LLM seul hallucine, cite des versions abrogées et mélange les droits. La base que l'on construit cette semaine, c'est la « connaissance externe vérifiable » du cours : chaque texte a une provenance (URL, empreinte SHA-256, méthode d'extraction).
- **Chapitre 02 (faits, règles, unification)** : la table `relations` est une **base de faits**, par exemple `modifie(ord_96_21, loi_90_11, art_12)` ou `abroge(X, loi_90_11, art_N)`. Le suivi des versions (brique 3) sera un petit moteur de règles à chaînage avant : *si une version de A commence en D1 et qu'un texte modifie A en D2 > D1, alors la version D1 est remplacée à partir de D2*. On prépare ces faits dès la S1 en gardant `text_type`, `text_number`, `sign_date` et `norm_rank` (hiérarchie des normes) pour chaque texte.

---

## 7. Risques et parades

| Risque | Parade |
|---|---|
| joradp.dz lent, bloquant ou robots.txt restrictif | Respecter le refus ; prévenir l'enseignant ; corpus de dépannage via `import-pdf`. La collecte reste démontrée sur quelques numéros. |
| Scans de 1990-1997 de mauvaise qualité (OCR) | DPI 300, mesurer l'erreur ; corriger à la main les articles de la loi 90-11 si besoin (texte de référence) ; WIPO Lex comme contrôle. |
| Texte arabe extrait dans le désordre | NFKC déjà appliqué ; tester tôt ; en dernier recours, OCR `ara` sur les pages concernées. |
| Intitulés atypiques (« Ordonnance n° 96-21 du 23 Safar 1417… ») | Chaque erreur constatée devient un test dans `tests/`. |
| Quota LLM | Pas de LLM dans la chaîne S1 (règles seulement) ; cache obligatoire dès le premier appel. |
| Travail inégal dans Git | Une branche par rôle, commits signés de chaque membre. |
