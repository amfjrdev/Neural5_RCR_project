# Recherche : BM25 vs embeddings (intfloat/multilingual-e5-small)

Corpus : 292 articles (loi 90-11, FR + AR, version initiale). Questions : 11 (hors périmètre exclu).
Une question est réussie si un article attendu (numéro de base) est dans les k premiers résultats.

| Cas | n | BM25 R@3 | BM25 R@5 | BM25 MRR | E5 R@3 | E5 R@5 | E5 MRR |
|---|---|---|---|---|---|---|---|
| Toutes questions, index FR+AR | 11 | 0.36 | 0.55 | 0.42 | 0.55 | 0.64 | 0.38 |
| Questions FR, index FR+AR | 6 | 0.33 | 0.50 | 0.39 | 0.50 | 0.67 | 0.45 |
| Questions AR, index FR+AR | 5 | 0.40 | 0.60 | 0.45 | 0.60 | 0.60 | 0.29 |
| Inter-langues : question FR -> articles AR seuls | 6 | 0.00 | 0.00 | 0.00 | 0.33 | 0.50 | 0.38 |
| Inter-langues : question AR -> articles FR seuls | 5 | 0.00 | 0.00 | 0.00 | 0.80 | 0.80 | 0.62 |
