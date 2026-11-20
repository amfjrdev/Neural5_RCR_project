# Audit des sources (semaine 1, responsable R2)

À compléter **avant tout téléchargement automatique**. Dater chaque vérification.

| Source | Usage dans le projet | Conditions / robots.txt (vérifié le …) | Décision |
|---|---|---|---|
| **JORADP** (joradp.dz) — PDF officiels FR `FTP/jo-francais/AAAA/FAAAANNN.pdf` et AR `FTP/jo-arabe/AAAA/AAAAANNN.pdf` | Source officielle de tous les textes | Vérifié le 14/11/2026 : pas de robots.txt (HTTP 404) ; aucune condition d'utilisation trouvée sur les pages lues (détail plus bas) | Pause ≥ 5 s, User-Agent identifié, pas de parallélisme |
| **Index Upgrowth** (upgrowth.dz/data/journal-officiel-archive.csv) | Liste des numéros et URL des PDF (env. 5 300 numéros). Colonnes : `year, issue, edition_fr, edition_ar, url_fr, url_ar, year_fully_probed` | Vérifié le 14/11/2026 : robots.txt autorise le CSV à tous. Licence CC BY 4.0 : citer « UpGrowth (2026), Index du Journal officiel algérien » | Téléchargé une fois, gardé dans `data/joradp_index.csv` |
| **WIPO Lex** — loi 90-11, texte FR (art. 1 à 158, version 1997) | Contrôle du découpage et de la qualité OCR | Vérifier les conditions de réutilisation | Contrôle seulement : ne contient pas les modifications postérieures à 1997 |
| **MTESS** (site du ministère du Travail) | Liste des textes du travail, à recouper | Vérifier les dates une par une | Aide pour construire `config/targets.yaml` |
| **Miroir SIA-Enna** | PDF classés par type | Accents parfois corrompus : corrigés par `fix_mojibake` | Secours seulement |
| **CLEISS** | Sécurité sociale (extension facultative) | — | Pas en S1 |
| ~~Recueil du ministère du Commerce~~ | — | **robots.txt interdit l'accès automatique** | **Ne pas aspirer** |

## Points d'attention relevés
- Les PDF **d'avant 2002 sont des scans** : OCR obligatoire (`fra` / `ara`).
- Les éditions FR et AR sont **publiées séparément** : un même numéro ne contient pas forcément les mêmes textes dans les deux langues, et certains numéros n'ont pas d'édition arabe (1962-1964).
- Seuls des **textes publics** sont envoyés au modèle de langage (règle d'usage de l'API).

## Textes de référence visés (à vérifier sur le PDF officiel)
| Texte | JO (d'après sources secondaires) | Vérifié ? |
|---|---|---|
| Loi 90-11 du 21/04/1990 (relations de travail) | n°17 du 25/04/1990 | ☐ |
| Lois 90-02, 90-03, 90-04 du 06/02/1990 | n°6 du 07/02/1990 | ☐ |
| Loi 91-29 du 21/12/1991 (modifie 90-11) | n°68 de 1991 | ☐ |
| Décret législatif 94-03 du 11/04/1994 (complète 90-11) | n°20 de 1994 | ☐ |
| Ordonnance 96-21 du 09/07/1996 (modifie 90-11) | n°43 de 1996 | ☐ |
| Ordonnances 97-02 et 97-03 du 11/01/1997 | n°3 du 12/01/1997 | ☐ |
| Loi 22-16 du 20/07/2022 (complète 90-11) | à trouver | ☐ |

## Vérifications du 14/11/2026 (22h56 à 22h58, heure d'Alger)

Méthode : pages ouvertes dans un navigateur sur le poste de l'équipe, avec un assistant IA (Claude). À déclarer dans la rubrique « Outils d'IA » du rapport. À refaire avec `python -m jurideazor check-robots` juste avant le premier téléchargement, et coller la sortie datée ici.

### joradp.dz
- `https://www.joradp.dz/robots.txt` : **HTTP 404** (page d'erreur du serveur). Pas de robots.txt, donc aucune restriction déclarée ; `collect/download.py` traite ce cas comme « autorisé ».
- Pages lues : accueil français (bandeau, menu, accueil, adresse) et page « Aide ». **Aucune condition d'utilisation, licence ou interdiction de téléchargement trouvée.** Non lues : pages en arabe et en anglais, « Contacts & Liens ».
- Motif d'URL confirmé par requête HEAD (sans télécharger le fichier) :
  - `/FTP/jo-francais/1990/F1990017.pdf` : 200, `application/pdf`, 958 334 octets ;
  - `/FTP/jo-arabe/1990/A1990017.pdf` : 200, `application/pdf`, 622 659 octets.
- **Attention :** les pages du site contiennent un dispositif anti-robots (script de détection, lien piège). Un script Python peut donc être refusé même sans robots.txt. Dans ce cas : ne pas contourner, prévenir l'enseignant, et passer par `import-pdf` (PDF téléchargé à la main ou corpus de dépannage).
- **Décision :** collecte limitée aux numéros de `config/targets.yaml`, une requête à la fois, pause d'au moins 5 s, User-Agent identifié avec l'email de l'équipe.

### upgrowth.dz
- `https://www.upgrowth.dz/robots.txt` : 200. Groupe `User-agent: *` : `Allow: /`, pas de `Crawl-delay`. Le fichier précise que les CSV ouverts, dont `journal-officiel-archive.csv`, restent accessibles à tous.
- **Interdits aux robots non nommés :** `/data/jo-fts/`, `/data/entities.json`, `/data/jo-ref-index.json`, `/data/nae-related.json`. L'index des références (JSON) ne doit donc pas être lu par script : pour trouver le numéro du JO de la loi 22-16, consulter les pages d'archives 2022 à la main.
- `https://www.upgrowth.dz/data/journal-officiel-archive.csv` : 200, `text/csv`, **5 288 lignes**, dernier numéro : n° 57 de 2026. En-tête conforme à `collect/index.py` : `year,issue,edition_fr,edition_ar,url_fr,url_ar,year_fully_probed`.
- Les six numéros visés (1990 n° 6 et n° 17, 1991 n° 68, 1994 n° 20, 1996 n° 43, 1997 n° 3) et les n° 1 à 5 de 2025 figurent dans l'index **en français et en arabe**. Cela montre que les fichiers existent, pas que les textes attendus s'y trouvent : la colonne « Vérifié ? » ci-dessus reste à cocher après lecture des PDF.
- Licence : CC BY 4.0 (page du jeu de données : https://www.upgrowth.dz/datasets/journal-officiel-1962-2026).

### Non vérifié à cette date
WIPO Lex, MTESS, miroir SIA-Enna, CLEISS, recueil du ministère du Commerce.
