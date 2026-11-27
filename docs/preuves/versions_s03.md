# Semaine 3 : versions datées de la loi 90-11 et relations entre textes

Généré par `python scripts/build_versions.py` (données : `data/amendements.yaml`).

## Textes modificatifs traités

| Texte | Entrée en vigueur | Opérations extraites |
|---|---|---|
| loi:91-29 | 1991-12-25 | 7 |
| decret_legislatif:94-03 | 1994-04-13 | 1 |
| ordonnance:96-21 | 1996-07-10 | 34 |
| ordonnance:97-02 | 1997-01-12 | 3 |
| ordonnance:97-03 | 1997-03-12 | 5 |

- decret_legislatif:94-03 : métadonnées corrigées (texte n° 249)
- ordonnance:97-02 : ajouté depuis data/text/fr/1997/F1997003.txt (texte n° 508)

Articles des textes modificatifs découpés : **40**.
Relations : **5** abroge, **34** complete, **11** modifie, **161** vise.

## Opérations (modifie / complète / crée / abroge) sur la loi 90-11

| Texte | Art. source | Action | Article 90-11 | Remarques |
|---|---|---|---|---|
| loi:91-29 | 2 | modifie | 73 |  |
| loi:91-29 | 3 | cree | 73-1 |  |
| loi:91-29 | 3 | cree | 73-2 |  |
| loi:91-29 | 3 | cree | 73-3 |  |
| loi:91-29 | 3 | cree | 73-4 |  |
| loi:91-29 | 3 | cree | 73-5 |  |
| loi:91-29 | 3 | cree | 73-6 |  |
| decret_legislatif:94-03 | 1 | cree | 87 bis |  |
| ordonnance:96-21 | 2 | complete | 12 |  |
| ordonnance:96-21 | 3 | cree | 12 bis |  |
| ordonnance:96-21 | 5 | complete | 31 |  |
| ordonnance:96-21 | 6 | modifie | 42 |  |
| ordonnance:96-21 | 7 | modifie | 44 |  |
| ordonnance:96-21 | 8 | modifie | 54 |  |
| ordonnance:96-21 | 9 | modifie | 73-4 |  |
| ordonnance:96-21 | 10 | modifie | 91 | en-tête cité Art. 9 ≠ cible 91 : à vérifier |
| ordonnance:96-21 | 11 | modifie | 93 |  |
| ordonnance:96-21 | 12 | cree | 93 bis |  |
| ordonnance:96-21 | 14 | modifie | 98 |  |
| ordonnance:96-21 | 15 | modifie | 100 | en-tête cité Art. 102 ≠ cible 100 : à vérifier |
| ordonnance:96-21 | 17 | modifie | 114 |  |
| ordonnance:96-21 | 18 | complete | 115 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 116 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 117 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 118 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 119 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 121 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 122 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 123 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 124 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 126 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 127 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 128 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 129 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 130 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 131 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 132 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 18 | complete | 133 | changement de terme (texte de l'article non réécrit) |
| ordonnance:96-21 | 19 | modifie | 134 |  |
| ordonnance:96-21 | 20 | cree | 143 bis |  |
| ordonnance:96-21 | 21 | cree | 146 bis |  |
| ordonnance:96-21 | 4 | complete | 13 | manuelle, à vérifier sur le PDF |
| ordonnance:97-02 | 2 | cree | 52 bis |  |
| ordonnance:97-02 | 3 | cree | 52 ter |  |
| ordonnance:97-02 | 4 | cree | 52 quater |  |
| ordonnance:97-03 | 8 | abroge | 22 | règle reprise dans ordonnance:97-03 art. 2 |
| ordonnance:97-03 | 8 | abroge | 23 | règle reprise dans ordonnance:97-03 art. 4 |
| ordonnance:97-03 | 8 | abroge | 24 | règle reprise dans ordonnance:97-03 art. 5 |
| ordonnance:97-03 | 8 | abroge | 25 | règle reprise dans ordonnance:97-03 art. 6 |
| ordonnance:97-03 | 8 | abroge | 26 | règle reprise dans ordonnance:97-03 art. 7 |

## Contrôles (critères du cahier des charges)

- loi:90-11 art. 12 au 1993-01-01 : version en vigueur depuis le 1990-04-21 (source : loi 90-11). ⚠ Cette version a été remplacée le 1996-07-10.
- loi:90-11 art. 12 au 2000-01-01 : version en vigueur depuis le 1996-07-10 (source : ordonnance 96-21).
- loi:90-11 art. 73 au 1990-06-01 : version en vigueur depuis le 1990-04-21 (source : loi 90-11). ⚠ Cette version a été remplacée le 1991-12-25.
- loi:90-11 art. 73 au 1995-01-01 : version en vigueur depuis le 1991-12-25 (source : loi 91-29).
- loi:90-11 art. 22 au 1995-01-01 : version en vigueur depuis le 1990-04-21 (source : loi 90-11).
- loi:90-11 art. 22 : ABROGÉ par ordonnance:97-03 depuis le 1997-03-12 (n'est plus en vigueur au 2000-01-01).
- loi:90-11 art. 87 bis : aucune version en vigueur au 1993-01-01 dans le corpus.
- loi:90-11 art. 87 bis au 2000-01-01 : version en vigueur depuis le 1994-04-13 (source : decret_legislatif 94-03).

## Historique complet de 3 articles réellement modifiés

### Article 12

| Du | Au | Statut | Source | Début du texte |
|---|---|---|---|---|
| 1990-04-21 | 1996-07-10 | remplacee | loi 90-11 | Art. 12. — Le contrat de travail peut être conclu pour une durée déterminée, à temps plein… |
| 1996-07-10 | … | en_vigueur | ordonnance 96-21 | Art. 12. — Le contrat de travail peut être conclu pour une durée déterminée, à temps plein… |

### Article 73

| Du | Au | Statut | Source | Début du texte |
|---|---|---|---|---|
| 1990-04-21 | 1991-12-25 | remplacee | loi 90-11 | Art. 73. — Le licenciement intervient dans le cas de fautes graves commises par le travail… |
| 1991-12-25 | … | en_vigueur | loi 91-29 | Art. 73. — Le licenciement à caractère disciplinaire intervient dans les cas de fautes gra… |

### Article 22

| Du | Au | Statut | Source | Début du texte |
|---|---|---|---|---|
| 1990-04-21 | 1997-03-12 | abrogee | loi 90-11 | Art. 22. — La durée légale de travail est fixée à quarante quatre (44) heures par semaine … |

## Points à vérifier

- ordonnance:96-21 art. 13 : « … est complété et rédigé comme suit : … La condition d'ancienneté prévue à l'alinéa 3 n'est pas requise … » (cible probable : art. 97)
- ordonnance:96-21 art. 16 : article absent de l'extraction
- ordonnance:96-21 art. 10 : cible 91 (l'OCR lit « Art. 9]. »)
- ordonnance:96-21 art. 15 : cible 100 (l'en-tête cité est mal lu)
