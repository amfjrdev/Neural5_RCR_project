# Évaluation du filtre « droit du travail »

Échantillon annoté : **20 textes** (prédiction « review » comptée comme « keep »).

| | Gold keep | Gold reject |
|---|---|---|
| **Prédit keep** | 6 (VP) | 4 (FP) |
| **Prédit reject** | 0 (FN) | 10 (VN) |

| Mesure | Valeur |
|---|---|
| Précision | 0.60 |
| Rappel | 1.00 |
| F1 | 0.75 |
| Exactitude | 0.80 |

Le rappel compte le plus ici : un texte du travail écarté à tort n'existera jamais pour l'assistant.

## Erreurs à analyser

- **faux positif** — JO 1991 n°68 (ar), texte 12 [score 6.0] : مرسوم تنفيذي رقم 91 - 517 مؤرخ في 15 جمادى الثانية عام 1412 الموافق 22 ديسمير سنة 1991 يتضمن تأسيس تعويض عن الخدمات الاستثنائية لفائدة بعض العمال التابعين للادر — *cas limite : indemnité de fonctionnaires (statut général de la fonction publique, ord. 66-133), hors loi 90-11*
- **faux positif** — JO 1994 n°20 (fr), texte 18 [score 3.08] : Arrêté du 21 Chaâbane 1414 correspondant au 2 février 1994 relatif à l'application des dispositions de l'article 160 du décret législatif n° 93-18 du 29 décembr — *cas limite : soutien des revenus des catégories défavorisées (aide sociale), hors droit du travail*
- **faux positif** — JO 1991 n°68 (ar), texte 10 [score 3.1] : مرسوم تنفيذي رقم 91 - 515 مؤرخ في 15 جمادى الثانية عام 1412 المؤافق 22 ديسمير سنة 1991, في وزارة التجهيز والسكن. - — *cas limite : indemnité de fonctionnaires (fonction publique), hors loi 90-11*
- **faux positif** — JO 1990 n°6 (fr), texte 5 [score 2.63] : Décret exécutif n° 90-49 du 6 février 1990 portant statut particulier des travailleurs de l'éducation. — *cas limite : statut particulier de fonctionnaires (éducation), hors loi 90-11*
