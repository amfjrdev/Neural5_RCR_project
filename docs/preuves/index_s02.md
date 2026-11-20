# Base vectorielle (semaine 2)

- Passages indexés : **985** (loi 90-11 article par article en FR et AR + 35 autres textes gardés par le filtre, découpés par article ou en fenêtres de 1 000 caractères).
- Modèle : intfloat/multilingual-e5-small (préfixes query: / passage:), vecteurs normalisés enregistrés dans data/index/multilingual-e5-small.npy.
- Index : FAISS IndexFlatIP (985 vecteurs, dimension 384) ; contrôle FAISS vs calcul direct sur les questions-test : **identique**.
- Rappel@5 sur l'index complet (article attendu de la 90-11 dans les 5 premiers) : **6/11**.

| Question | Langue | Article attendu dans le top 5 | 3 premiers résultats |
|---|---|---|---|
| Q01 | fr | oui | loi:90-11 art.35 (fr) ; loi:90-11 art.33 (fr) ; loi:90-11 art.37 (fr) |
| Q02 | fr | oui | loi:90-11 art.11 (fr) ; loi:90-11 art.12 (fr) ; loi:90-11 art.14 (fr) |
| Q03 | fr | non | loi:90-11 art.142 (fr) ; loi:90-11 art.69 (fr) ; decret_executif:91-515 art.4 (fr) |
| Q04 | fr | oui | loi:90-11 art.7 (fr) ; loi:90-11 art.5 (fr) ; loi:90-03 art.9 (fr) |
| Q05 | fr | non | loi:91-29 art.73 (fr) ; loi:91-29 art.73-4 (fr) ; loi:90-11 art.53 (fr) |
| Q06 | fr | non | loi:91-29 art.- (fr) ; decret_legislatif:94-04 art.- (fr) ; ordonnance:96-21 art.- (fr) |
| QA01 | ar | oui | loi:90-11 art.36 (ar) ; loi:90-11 art.33 (ar) ; loi:90-11 art.34 (ar) |
| QA02 | ar | oui | loi:90-11 art.13 (ar) ; loi:90-11 art.11 (ar) ; loi:90-11 art.6 (ar) |
| QA03 | ar | oui | loi:90-04 art.4 (ar) ; loi:90-03 art.12 (ar) ; loi:90-11 art.22 (ar) |
| QA04 | ar | non | loi:90-11 art.13 (ar) ; loi:90-11 art.11 (ar) ; ordonnance:21-96 art.12 (ar) |
| QA05 | ar | non | loi:90-11 art.72 (ar) ; loi:91-28 art.73 (ar) ; loi:91-28 art.3 (ar) |
