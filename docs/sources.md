# Audit des sources (semaine 1, responsable R2)

À compléter **avant tout téléchargement automatique**. Dater chaque vérification.

| Source | Usage dans le projet | Conditions / robots.txt (vérifié le …) | Décision |
|---|---|---|---|
| **JORADP** (joradp.dz) — PDF officiels FR `FTP/jo-francais/AAAA/FAAAANNN.pdf` et AR `FTP/jo-arabe/AAAA/AAAAANNN.pdf` | Source officielle de tous les textes | *coller ici la sortie de `python -m jurideazor check-robots`* ; lire les CGU | Pause ≥ 5 s, User-Agent identifié, pas de parallélisme |
| **Index Upgrowth** (upgrowth.dz/data/journal-officiel-archive.csv) | Liste des numéros et URL des PDF (env. 5 300 numéros). Colonnes : `year, issue, edition_fr, edition_ar, url_fr, url_ar, year_fully_probed` | Licence CC BY 4.0 : citer « UpGrowth (2026), Index du Journal officiel algérien » | Téléchargé une fois, gardé dans `data/joradp_index.csv` |
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
