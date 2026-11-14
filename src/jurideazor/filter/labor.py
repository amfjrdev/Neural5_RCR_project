"""Filtre « ce texte concerne-t-il le droit du travail ? » (FR et AR).

Méthode de base, explicable et mesurable : règles d'exclusion + score par
mots-clés pondérés. Le score donne trois décisions :
    keep   : à garder
    review : à vérifier à la main (zone grise)
    reject : à écarter
Les visas (« Vu la loi... », « بمقتضى ») sont retirés avant de compter, car
presque tous les textes citent le ministre du travail ou la loi 90-11 en visa.

Ce filtre est la *baseline* : sa qualité est mesurée sur un échantillon annoté
(cli: sample-filter puis eval-filter). Une version assistée par le LLM pourra
être comparée plus tard sur le même échantillon.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..extract.clean import fold_ar, fold_fr

# ------------------------------------------------------------------ FR (plié) --
FR_REJECT = [
    (r"portant nomination", "nomination"),
    (r"mettant fin aux? fonctions", "fin de fonctions"),
    (r"portant naturalisation", "naturalisation"),
    (r"changement de nom", "changement de nom"),
    (r"delegation de signature", "délégation de signature"),
    (r"(portant|relatif a l[a'e]?)\s*(transfert|virement|repartition) de credits", "crédits budgétaires"),
    (r"portant (attribution|decernement) de? (la )?medaille", "distinction"),
    (r"^avis\b|communique", "avis / communiqué"),
    (r"portant (approbation|ratification) .*convention .*(pret|financement)", "accord de financement"),
]
FR_KEYWORDS = [  # (motif, poids)
    (r"relations? (individuelles? |collectives? )?de travail", 4),
    (r"contrats? de travail", 4),
    (r"duree legale du travail|duree du travail", 4),
    (r"licenciements?", 3), (r"preavis", 3), (r"periode d'essai", 3), (r"demission", 2),
    (r"droit syndical|organisations? syndicales?|exercice du droit syndical", 4),
    (r"\bgreve\b|droit de greve", 4),
    (r"conflits? (collectifs?|individuels?) (du|de) travail", 4),
    (r"conventions? (et accords )?collectifs?|conventions? collectives?", 3),
    (r"inspection du travail|inspecteurs? du travail", 4),
    (r"hygiene.{0,30}securite|medecine du travail|securite au travail", 3),
    (r"salaire national minimum garanti|\bsnmg\b", 4),
    (r"\bsalaires?\b|remuneration", 2),
    (r"conges? (annuels?|payes?|de maternite)|\bconges?\b", 2),
    (r"heures supplementaires|repos hebdomadaire|travail de nuit", 3),
    (r"travailleurs?\b", 2), (r"employeurs?\b", 2),
    (r"\btravail\b", 2),
    (r"reglement interieur", 2),
    (r"accidents? du travail|maladies? professionnelles?", 3),   # extension sécurité sociale
    (r"securite sociale|assurances? sociales?|retraite|assurance[- ]chomage", 2),
    (r"\bemploi\b|\bchomage\b|apprentissage", 1),
]
FR_SECTION_BONUS = re.compile(r"ministere du travail")

# ------------------------------------------------------------------ AR (plié) --
AR_REJECT = [
    (r"يتضمن\s+تعيين", "nomination"),
    (r"انهاء\s+مهام", "fin de fonctions"),
    (r"التجنس", "naturalisation"),
    (r"تغيير\s+اللقب", "changement de nom"),
    (r"تفويض\s+الامضاء", "délégation de signature"),
    (r"(تحويل|نقل)\s+اعتماد", "crédits budgétaires"),
]
AR_KEYWORDS = [
    (r"علاقات\s+العمل", 4), (r"عقد\s+العمل|عقود\s+العمل", 4),
    (r"المده\s+القانونيه\s+للعمل", 4), (r"التسريح", 3), (r"الاشعار\s+المسبق", 3),
    (r"فتره\s+التجريب", 3), (r"الاستقاله", 2),
    (r"الحق\s+النقابي|التنظيمات\s+النقابيه|النقابي", 4), (r"الاضراب", 4),
    (r"النزاعات\s+(الجماعيه|الفرديه)", 4), (r"الاتفاقيات\s+الجماعيه|الاتفاقيات\s+والاتفاقات\s+الجماعيه", 3),
    (r"مفتشيه\s+العمل|مفتشي\s+العمل", 4),
    (r"الوقايه\s+الصحيه\s+والامن|طب\s+العمل", 3),
    (r"الاجر\s+الوطني\s+الادني\s+المضمون", 4), (r"الاجور|الاجر", 2),
    (r"العطل|عطله", 2), (r"الساعات\s+الاضافيه|الراحه\s+الاسبوعيه|العمل\s+الليلي", 3),
    (r"العمال|العامل", 2), (r"المستخدم", 2), (r"\bالعمل\b", 2),
    (r"النظام\s+الداخلي", 2),
    (r"حوادث\s+العمل|الامراض\s+المهنيه", 3),
    (r"الضمان\s+الاجتماعي|التامينات\s+الاجتماعيه|التقاعد|التامين\s+عن\s+البطاله", 2),
    (r"التشغيل|البطاله|التمهين", 1),
]
AR_SECTION_BONUS = re.compile(r"وزاره\s+العمل")

FR_VISA = re.compile(r"^\s*(vu|-?\s*vu)\b", re.I)
AR_VISA = re.compile(r"^\s*-?\s*(و?بمقتضي|بناء\s+علي|و?بعد)")


@dataclass
class Decision:
    relevance: str          # keep | review | reject
    score: float
    reasons: list[str]
    is_circular: bool


def _strip_visas(body: str, lang: str) -> str:
    pat = AR_VISA if lang == "ar" else FR_VISA
    fold = fold_ar if lang == "ar" else fold_fr
    return "\n".join(l for l in body.splitlines() if not pat.match(fold(l)))


def classify(title: str, body: str, section: str | None, text_type: str | None, lang: str,
             keep_threshold: float = 4.0, review_threshold: float = 2.0) -> Decision:
    fold = fold_ar if lang == "ar" else fold_fr
    rejects = AR_REJECT if lang == "ar" else FR_REJECT
    keywords = AR_KEYWORDS if lang == "ar" else FR_KEYWORDS
    bonus = AR_SECTION_BONUS if lang == "ar" else FR_SECTION_BONUS
    t, sec = fold(title), fold(section or "")
    is_circ = text_type in ("circulaire", "instruction")

    for pat, label in rejects:
        if re.search(pat, t):
            return Decision("reject", 0.0, [f"exclusion: {label}"], is_circ)

    score, reasons = 0.0, []
    for pat, w in keywords:                       # titre : poids plein
        if re.search(pat, t):
            score += w
            reasons.append(f"titre:{pat.split('|')[0][:30]}(+{w})")
    if bonus.search(sec):
        score += 2
        reasons.append("rubrique ministère du travail(+2)")

    b = fold(_strip_visas(body, lang))
    n_words = max(len(b.split()), 1)
    hits = sum(len(re.findall(pat, b)) * w for pat, w in keywords)
    density = hits / n_words * 100                # points pondérés pour 100 mots
    body_pts = min(density, 4.0)                  # plafonné : le titre reste décisif
    if body_pts >= 0.5:
        score += body_pts
        reasons.append(f"corps:densite {density:.1f}(+{body_pts:.1f})")

    if score >= keep_threshold:
        rel = "keep"
    elif score >= review_threshold:
        rel = "review"
    else:
        rel = "reject"
    if is_circ and rel != "reject":
        reasons.append("circulaire : interprétation de l'administration")
    return Decision(rel, round(score, 2), reasons, is_circ)
