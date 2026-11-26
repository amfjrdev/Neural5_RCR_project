# Ontologie minimale de Jurideazor (semaine 3)

But : représenter les textes du droit du travail, leurs articles, **les versions successives** de chaque article et les liens entre textes. Ce sont ces liens qui permettent de répondre « quelle règle était en vigueur à telle date ? » et « ce texte est-il encore valable ? ».

Code : `src/jurideazor/ontology.py`. Le graphe est construit par `scripts/build_graph.py` à partir de la base SQLite.

## 1. Classes (types de nœuds)

| Classe | Identifiant | Attributs principaux | Table SQLite |
|---|---|---|---|
| **Texte** | `loi:90-11`, `ordonnance:96-21` | type, numéro, date de signature, **rang** (hiérarchie des normes), titre, lien source, circulaire (oui/non), présent dans le corpus (oui/non) | `texts` |
| **Article** | `loi:90-11#art.12` | texte, numéro (`12`, `12 bis`, `73-4`) | `articles` |
| **Version** | `version:<id>` | langue, **valid_from**, **valid_to**, **status** (`en_vigueur`, `remplacee`, `abrogee`), extrait | `article_versions` |
| **Concept** | `concept:cdd` | libellé (21 thèmes du périmètre : CDD, période d'essai, licenciement, préavis, repos, congé, salaire…) | — (lexique FR/AR) |

**Hiérarchie des normes** (`norm_rank`) : 1 Constitution · 2 loi, ordonnance, décret législatif · 3 décret présidentiel ou exécutif · 4 arrêté · 5 circulaire, instruction (« interprétation de l'administration »).

## 2. Relations (types d'arêtes)

| Relation | De → vers | Sens | Source de l'information |
|---|---|---|---|
| `contient` | Texte → Article | le texte est découpé en articles | `split_articles.py`, `build_versions.py` |
| `a_version` | Article → Version | versions successives de l'article | `article_versions` |
| `remplacee_par` | Version → Version | ordre chronologique (même langue) | dates `valid_from` |
| `introduit` | Texte → Version | texte qui a créé cette version | `source_text_id` |
| `modifie` | Texte → Article | l'article est réécrit | extraction (`amendments.py`) |
| `complete` | Texte → Article | ajout d'un alinéa, ou création d'un article (12 bis, 73-1…) | extraction |
| `abroge` | Texte → Article | l'article n'est plus en vigueur | extraction |
| `vise` | Texte → Texte | le texte cite un autre texte dans ses visas (« Vu la loi n° … ») | regex sur les visas |
| `repris_dans` | Article → Article | la règle d'un article abrogé se trouve désormais ailleurs | `data/amendements.yaml` (renvois) |
| `traite_de` | Article → Concept | thème juridique de l'article (version en vigueur) | mots-clés FR/AR |

## 3. Règles (utilisées dès maintenant, développées en semaine 4)

1. **Version en vigueur à une date D** : la version dont `valid_from ≤ D < valid_to` (ou `valid_to` vide). Sans date, on prend D = aujourd'hui. → `jurideazor.versions.version_at`.
2. **Modification** : si un texte T, en vigueur à la date D2, modifie l'article A, alors la version courante de A se termine en D2 (`status = remplacee`) et une nouvelle version commence en D2.
3. **Abrogation** : si T abroge A en D2, la version courante se termine en D2 (`status = abrogee`). **Un article abrogé n'est jamais présenté comme actuel** ; on indique où la règle a été reprise (`repris_dans`).
4. **Entrée en vigueur** : date de publication au Journal officiel, sauf disposition contraire du texte (ex. ordonnance 97-03, art. 9 : deux mois après la publication).
5. **Conflit entre textes** : le rang le plus petit (norme supérieure) l'emporte ; à rang égal, le texte le plus récent l'emporte (à implémenter en S4).
6. **Divergence FR/AR** (ex. art. 18 : 10 mois en FR contre 6 mois en AR) : afficher les deux et le signaler (S4/S5).
7. **Langue** : les textes modificatifs sont traités en français. Quand une version française est remplacée, la version arabe de la même date est fermée aussi ; elle ne sera donc jamais présentée comme actuelle.

## 4. Exemple

```
ordonnance:97-03 ──abroge──▶ loi:90-11#art.22 ──a_version──▶ version (1990-04-21 → 1997-03-12, abrogee)
        │                           │
        └──contient──▶ ordonnance:97-03#art.2 ◀──repris_dans──┘     (« durée légale : 40 heures »)
```
Question « Quelle est la durée légale du travail ? » (sans date) → l'art. 22 est abrogé → on suit `repris_dans` → ordonnance 97-03, art. 2 : **40 h**. Pour une question datée de 1995 → art. 22 version 1990 : **44 h**.
