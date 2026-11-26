# Semaine 3 : graphe de connaissances

Construit par `python scripts/build_graph.py` depuis la base SQLite (après `build_versions.py`). Ontologie : `docs/ontologie.md`.

## Taille du graphe

| Type de nœud | Nombre |
|---|---|
| Article | 212 |
| Concept | 21 |
| Texte | 92 |
| Version | 387 |

| Type d'arête | Nombre |
|---|---|
| a_version | 387 |
| abroge | 5 |
| complete | 34 |
| contient | 212 |
| introduit | 242 |
| modifie | 11 |
| remplacee_par | 31 |
| repris_dans | 5 |
| traite_de | 343 |
| vise | 161 |

## Requêtes d'exemple sur le graphe

**1. Quels textes modifient, complètent ou abrogent la loi 90-11 ?** decret_legislatif:94-03, loi:91-29, ordonnance:96-21, ordonnance:97-02, ordonnance:97-03.

**2. Articles de la loi 90-11 les plus touchés :** art. 73-4 (2), art. 73 (1), art. 73-1 (1), art. 73-2 (1), art. 73-3 (1), art. 73-5 (1), art. 73-6 (1), art. 87 bis (1).

**3. Textes les plus cités dans les visas (« Vu … ») :** loi:90-02 (9), loi:90-11 (9), ordonnance:66-156 (8), loi:90-03 (8), loi:90-04 (8), loi:90-14 (5), loi:88-01 (4), loi:78-12 (4).

**4. Articles de la 90-11 qui traitent du CDD :** 12, 14, 19, 66, 117, 146 bis.

**5. Articles de la 90-11 qui traitent du licenciement :** 66, 68, 69, 70, 71, 72, 73, 73-1, 73-2, 73-3, 73-4, 73-5, 94, 113, 148.

**6. Concepts les plus présents :** Salaire et rémunération (48), Conventions et accords collectifs (44), Participation des travailleurs (33), Contrat de travail (29), Congé annuel et absences (28), Sanctions pénales (amendes) (21).

**7. Chemin dans le graphe** (abrogation puis reprise de la règle) : ordonnance:97-03 → ordonnance:97-03#art.2 ; loi:90-11#art.22 → repris_dans → ordonnance:97-03#art.2.

## Fichiers

- `data/graph/graphe.graphml` (Gephi, yEd), `data/graph/graphe.json`
- `docs/preuves/graphe_s03.html` : vue interactive (ouvrir dans un navigateur)
- `docs/preuves/graphe_s03.png` : vue statique
