# Test du LLM seul (sans RAG) - modèle openai/gpt-oss-120b

Appels réels : 12 | réponses servies par le cache : 0

## Q01 (1-directe, fr)
**Question :** Quel est le jour de repos hebdomadaire légal ?

**Réponse :**

En droit du travail algérien, le jour de repos hebdomadaire légal est le dimanche. Cette règle est prévue à l’article **33** du **Code du travail algérien**, qui dispose que « le repos hebdomadaire est fixé au dimanche, sauf disposition conventionnelle ou accord d’entreprise prévoyant un autre jour ». Ainsi, sauf convention contraire, chaque salarié bénéficie d’un repos chaque dimanche.

**Erreur constatée (regle_fausse; citation_inventee) :** Dit 'dimanche'. Art. 33 loi 90-11 (corpus, JO 17/1990) : repos hebdomadaire fixé au vendredi. N° d'article juste, contenu et citation inventés ; parle d'un 'Code du travail' au lieu de la loi 90-11.

## Q02 (1-directe, fr)
**Question :** Un contrat de travail peut-il être conclu à l'oral ?

**Réponse :**

Oui, le contrat de travail peut être conclu à l’oral en Algérie. L’article 12 du Code du travail algérien dispose : « Le contrat de travail peut être conclu verbalement, sauf dispositions contraires prévues par la loi ou par les conventions collectives. » Cependant, pour les emplois soumis à des formalités particulières (ex. : travail des femmes enceintes, travailleurs étrangers, postes de direction), la loi impose une forme écrite (art. 13 et art. 14). En pratique, il est fortement recommandé de formaliser le contrat par écrit afin de pouvoir en justifier les termes en cas de litige. Ainsi, l’oral est légal, mais l’écrit reste la meilleure garantie de sécurité juridique.

**Erreur constatée (mauvais_article; citation_inventee) :** Conclusion plausible mais cite l'art. 12 (= CDD). La forme du contrat relève des art. 9-11 (forme libre, preuve par tout moyen, CDI présumé sans écrit). Exceptions art. 13/14 inventées.

## Q03 (2-combinee, fr)
**Question :** Dans quels cas un CDD est-il autorisé ?

**Réponse :**

En Algérie, le contrat à durée déterminée (CDD) n’est autorisé que dans les cas prévus à l’article **12** du Code du travail (Décret n° 86‑05 du 11 février 1986).  
1. Remplacement d’un salarié absent (congé, maladie, maternité, etc.).  
2. Exécution d’une tâche temporaire ou d’un surcroît d’activité clairement limité dans le temps.  
3. Travail saisonnier ou lié à une activité naturellement cyclique.  
4. Réalisation d’une mission précise, d’un projet ou d’une prestation dont la durée est déterminée à l’avance.  
5. Tout autre motif justifié par l’employeur et mentionné explicitement dans le contrat, sous réserve du respect du plafond de renouvellement fixé à l’article **13** du même code.

**Erreur constatée (texte_invente; cas_inventes) :** N° d'article 12 juste, mais l'attribue à un 'Décret 86-05' absent du corpus. Ajoute 'tout autre motif justifié' alors que l'art. 12 limite aux cas 'expressément prévus' ; oublie le cas 'contrats de travaux ou de prestation non renouvelables'.

## Q04 (2-combinee, fr)
**Question :** Quelles sont les obligations de l'employeur en matière d'hygiène et de sécurité ?

**Réponse :**

En droit du travail algérien, l’employeur doit assurer la sécurité et protéger la santé des travailleurs (art. 13 du Code du travail). Il doit mettre en place les mesures de prévention nécessaires, notamment l’équipement de protection individuelle et collective (art. 14). Il est tenu d’informer, de former et de sensibiliser le personnel aux risques liés à l’activité (art. 15). L’employeur doit également veiller à la conformité des locaux et des installations aux normes d’hygiène et de sécurité en vigueur (art. 16). Enfin, il doit instaurer un service de prévention ou désigner un responsable de la sécurité et tenir à jour le registre des accidents du travail (art. 17).

**Erreur constatée (articles_inventes) :** Cite les art. 13 à 17 de la loi 90-11 : dans le corpus ils portent sur le temps partiel (13), la requalification du CDD (14), l'âge minimum (15), les handicapés (16), la non-discrimination (17). Aucun ne traite d'hygiène et sécurité (seul l'art. 5 la cite comme droit).

## Q05 (3-cas-pratique, fr)
**Question :** Un salarié est licencié sans motif : quels recours et quelles garanties prévoient les textes ?

**Réponse :**

En droit algérien, le licenciement doit être motivé : l’article 13 de l’Ordonnance n° 66‑03 du 2 juillet 1966 portant Code du travail dispose que « tout licenciement doit être justifié par une cause réelle et sérieuse ». En l’absence de motif, le salarié peut saisir le tribunal du travail dans les 30 jours suivant la notification du licenciement (article 15 du même code). Le juge peut alors annuler le licenciement et ordonner la réintégration du salarié ou, à défaut, condamner l’employeur à verser une indemnité compensatrice équivalente à la rémunération que le salarié aurait perçue pendant la durée du préavis (article 14). Par ailleurs, le salarié bénéficie d’une indemnité de licenciement calculée selon son ancienneté (article 14, alinéa 2). Ces garanties sont donc assurées par les articles 13, 14 et 15 du Code du travail algérien.

**Erreur constatée (texte_hors_corpus; chiffres_non_sources) :** S'appuie sur une 'Ordonnance 66-03' absente du corpus, ignore la loi 90-11 (art. 73 et suivants) et la loi 90-04 (conflits individuels). Délai de 30 jours non sourcé.

## Q06 (3-datee, fr)
**Question :** Que prévoyait la loi sur les cas de recours au CDD en 1993, et qu'est-ce qui a changé depuis ?

**Réponse :**

La loi n° 90‑11 du 21 avril 1990, article 13, autorisait le contrat à durée déterminée (CDD) uniquement pour le remplacement d’un salarié absent ou pour l’exécution d’une tâche temporaire clairement définie, en limitant la durée maximale à 12 mois renouvelable une fois.  
La loi n° 06‑02 du 23 février 2006, article 12, a élargi les motifs de recours au CDD en y incluant les besoins ponctuels d’activité, les travaux saisonniers et les missions de formation, tout en portant la durée maximale à 24 mois, renouvelable une fois.  
Par ailleurs, l’article 14 de la même loi a introduit l’obligation d’inscrire le CDD dans le registre du personnel et de préciser le motif exact, sous peine de requalification en CDI.  
Depuis la réforme de 2015 (décret exécutif n° 15‑09 du 30 janvier 2015, article 5), le CDD ne peut plus être utilisé pour pourvoir durablement un poste permanent, renforçant ainsi la protection contre l’abus du recours à ces contrats.  
En résumé, le cadre du CDD est passé d’une utilisation très restreinte (1993) à une plus grande souplesse encadrée par des plafonds de durée et des exigences de justification plus strictes.

**Erreur constatée (versions_inventees; mauvais_article) :** Attribue le CDD à l'art. 13 (= temps partiel ; le CDD est l'art. 12). Cite une 'loi 06-02' et un 'décret exécutif 15-09' absents du corpus ; durées 12/24 mois non présentes dans l'art. 12. Les textes modificatifs du corpus (91-29, 96-21) ne sont pas mentionnés.

## Q07 (hors-perimetre, fr)
**Question :** Quelle est la durée du préavis en France ?

**Réponse :**

En France, la durée du préavis dépend du type de contrat et de l’ancienneté du salarié :

1. **Contrat à durée indéterminée (CDI)** – article L1237‑1 du Code du travail : le préavis est fixé par la convention collective ou, à défaut, par les usages de la profession ; à défaut de disposition, il est généralement de **1 mois** pour les salariés ayant moins de 2 ans d’ancienneté et de **2 mois** au‑delà (article L1237‑2).  
2. **Contrat à durée déterminée (CDD)** – article L1243‑2 : le préavis s’applique uniquement en cas de rupture anticipée (démission ou licenciement) et est proportionnel à la durée du contrat, généralement **1 jour** par semaine de contrat, avec un minimum de 1 semaine.  
3. **Licenciement économique ou pour motif personnel** – article L1234‑1 : le préavis suit les mêmes règles que pour le CDI, sauf dispositions plus favorables prévues par la convention collective.  

Ainsi, la durée du préavis varie principalement selon l’ancienneté et les accords collectifs applicables.

**Erreur constatée (hors_perimetre_non_refuse) :** Répond sur le droit français au lieu de refuser. Le système attendu doit dire : 'je ne trouve pas de règle dans le corpus'.

## QA01 (1-directe, ar)
**Question :** ما هو يوم الراحة الأسبوعية القانوني؟

**Réponse :**

يحدد القانون الجزائري للعمل أن لكل عامل حقًا في يوم راحة أسبوعي لا يقل عن 24 ساعة متتالية. هذا ما نصّ عليه **المادة 31 من قانون العمل (قانون رقم 90‑11 المؤرخ 22 أغسطس 1990)**، والتي تنص صراحةً على أن «يُمنح العامل يومًا واحدًا على الأقل من الراحة الأسبوعية يُعَدّ إجازةً مدفوعة الأجر». وعادةً ما يُطبق هذا اليوم في **يوم الجمعة** كونه اليوم التقليدي للراحة في معظم القطاعات، إلا أن صاحب العمل والعمال يمكنهم الاتفاق على يوم آخر بشرط ألا يقل عن 24 ساعة في الأسبوع. وبالتالي، فإن يوم الراحة الأسبوعية القانوني هو على الأقل يوم واحد يُعطى للعمال وفقًا للمادة 31 من قانون العمل.

**Erreur constatée (mauvais_article; date_fausse) :** Cite l'art. 31 (= heures supplémentaires dans le corpus) au lieu de l'art. 33 ; date de la loi 90-11 donnée au 22 août 1990 au lieu du 21 avril 1990. Présente le vendredi comme simple usage alors que l'art. 33 le fixe.

## QA02 (1-directe, ar)
**Question :** هل يمكن إبرام عقد العمل شفهيا؟

**Réponse :**

نعم، يمكن إبرام عقد العمل شفهياً وفقاً للمادة 12 من قانون العمل الجزائري (المجلة 1 – قانون 90‑11).  
هذه المادة تنص على أن «العقد يُعقد كتابةً أو شفاهةً، ولا يلزم أن يكون مكتوباً إلا في الحالات التي يقتضيها القانون أو الاتفاق بين الطرفين».  
مع ذلك، يُفضَّل دائماً توثيق العقد كتابةً لتجنب النزاعات وإثبات الشروط المتفق عليها.  
في حال عدم وجود عقد مكتوب، يظل العقد الشفهي ساري المفعول ويُطبق عليه أحكام القانون العامة.  
إذن، لا يُعدّ العقد الشفهي غير قانوني، لكنه قد يواجه صعوبات في الإثبات أمام القضاء.

**Erreur constatée (mauvais_article; citation_inventee) :** Cite l'art. 12 (= CDD) au lieu des art. 9-11 ; citation inventée ; référence 'المجلة 1' sans sens.

## QA03 (1-directe, ar)
**Question :** ما هي المدة القصوى لفترة التجربة؟

**Réponse :**

مدة فترة التجربة في القانون الجزائري لا تتجاوز **ثلاثة أشهر** للعمال العاديين، ويمكن تمديدها إلى **ستة أشهر** فقط لل cadres (الإداريين والمهنيين) إذا نصت العقود على ذلك. وهذا ما ينص عليه **المادة 15 من قانون العمل الجزائري** (قانون رقم 90‑11 المتعلق بتنظيم علاقات العمل). وبالتالي، لا يجوز تجاوز هذه الحدود إلا إذا تم الاتفاق صراحةً على تمديدها وفق الشروط المحددة في النص. أي تجاوز للمدة المقررة يعتبر غير قانوني ويستوجب تعديل العقد أو إلغاء الفترة الإضافية.

**Erreur constatée (mauvais_article; chiffres_faux) :** Cite l'art. 15 (= âge minimum) au lieu de l'art. 18. Durées 3/6 mois fausses : l'édition arabe officielle (JO 17/1990, p. 564, art. 18) dit ستة (06) أشهر, portée à 12 mois pour la haute qualification. NB : l'édition française du même JO (p. 490) dit 'dix (10) mois' -> divergence FR/AR dans les textes officiels eux-mêmes (voir docs/preuves/verification_pdf.md).

## QA04 (2-combinee, ar)
**Question :** ما هي الحالات التي يجوز فيها إبرام عقد عمل محدد المدة؟

**Réponse :**

في القانون الجزائري (قانون العمل رقم 90‑11) تُحدَّد الحالات التي يجوز فيها إبرام عقد عمل محدد المدة في المادة 12 من هذا القانون.  
1‑ عندما يكون العمل مؤقتًا بطبيعته (مثلاً أعمال موسمية أو مؤقتة).  
2‑ عندما يكون العامل مطلوبًا لإنجاز مهمة محددة أو مشروع معين يحدده صاحب العمل.  
3‑ عندما يُستدعى العامل لتغطية غياب مؤقت لعامل آخر (إجازة، إجازة مرضية، إلخ).  
4‑ عندما يُستدعى العامل لتلبية احتياجات مؤقتة في حجم العمل (زيادة مؤقتة في الإنتاج).  
5‑ في جميع هذه الحالات يجب أن يُذكر في العقد سبب التحديد الزمني وتاريخ انتهاء العمل، وإلا يُعتبر العقد غير محدد المدة وفقًا للمادة 13 من نفس القانون.

**Erreur constatée (cas_inventes; mauvais_article) :** Art. 12 juste, mais cas 'mission/projet' et 'besoins temporaires' reformulés/inventés ; attribue à l'art. 13 (= temps partiel) la requalification, qui est l'art. 14.

## QA05 (1-directe, ar)
**Question :** هل يحق للمستخدم تسريح عامل دون إشعار مسبق؟

**Réponse :**

لا يجوز لصاحب العمل في الجزائر فصل العامل دون إعطائه إشعاراً مسبقاً، إلا في حالة ارتكاب العامل خطأً جسيمًا يستدعي الفصل الفوري. وهذا ما ينص عليه **المادة 13 من قانون العمل الجزائري** التي تفرض على صاحب العمل إبلاغ العامل بمدة الإشعار المقررة (ثلاثة أشهر للعمال غير المؤقتين) قبل إنهاء العقد. في حال وجود خطأ جسيم، يسمح **بالمادة 14** بإنهاء العقد فورًا دون إشعار، بشرط إثبات الخطأ أمام المحكمة. وبالتالي، لا يمكن الفصل دون إشعار إلا إذا تم إثبات الخطأ الجسيم وفق الإجراءات القانونية.

**Erreur constatée (mauvais_article; chiffre_invente) :** Cite les art. 13/14 (temps partiel / requalification CDD) ; le licenciement pour faute grave relève de l'art. 73. Préavis de 'trois mois' non sourcé.

## Synthèse (vérifiée contre le texte officiel de la loi 90-11, JO n° 17/1990, extrait du corpus)
| Indicateur | Résultat |
|---|---|
| Réponses avec au moins une erreur | 12 / 12 |
| Bon n° d'article cité | 3 / 12 (Q01 art. 33, Q03 et QA04 art. 12), mais contenu faux ou incomplet |
| Textes inventés ou absents du corpus | 4 (décret 86-05, ordonnance 66-03, loi 06-02, décret exécutif 15-09) |
| Règle fausse sur la question la plus simple | Q01 : dimanche au lieu du vendredi (art. 33) |
| Question hors périmètre refusée | 0 / 1 (répond sur le droit français) |
| Gestion des versions (Q06) | versions et textes modificatifs inventés |

Conclusion : le LLM seul cite des articles avec assurance mais se trompe d'article ou de contenu ; il ne refuse pas le hors-périmètre. D'où la nécessité de la recherche dans le corpus (RAG) et de la vérification des citations.
Annotation : pré-annotation assistée par IA (Claude), vérifiée sur les images des PDF officiels FR et AR du JO n° 17/1990 (art. 9-12, 18, 31, 33) : voir verification_pdf.md.
