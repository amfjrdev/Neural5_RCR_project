"""Ontologie minimale de Jurideazor (semaine 3). Voir docs/ontologie.md.

Classes (types de nœuds) : Texte, Article, Version, Concept.
Relations (types d'arêtes) :
  Texte   --contient-->      Article     (un texte est découpé en articles)
  Article --a_version-->     Version     (versions successives d'un article)
  Version --remplacee_par--> Version     (chaîne chronologique)
  Texte   --introduit-->     Version     (texte qui a créé cette version)
  Texte   --modifie|complete|abroge--> Article   (opérations d'un texte modificatif)
  Texte   --vise-->          Texte       (visas « Vu la loi n° … »)
  Article --repris_dans-->   Article     (article abrogé dont la règle est reprise ailleurs)
  Article --traite_de-->     Concept     (thème juridique, repéré par mots-clés FR/AR)
"""
from __future__ import annotations

import re
import unicodedata

NODE_TYPES = ("Texte", "Article", "Version", "Concept")
EDGE_TYPES = ("contient", "a_version", "remplacee_par", "introduit", "modifie", "complete", "abroge",
              "vise", "repris_dans", "traite_de")

# Concepts du périmètre (cahier des charges) et mots-clés pour les repérer dans les articles (FR / AR).
CONCEPTS: dict[str, dict] = {
    "contrat_de_travail": {"label": "Contrat de travail", "fr": ["contrat de travail", "relation de travail"], "ar": ["عقد العمل", "علاقة العمل"]},
    "cdd": {"label": "Contrat à durée déterminée (CDD)", "fr": ["durée déterminée"], "ar": ["محددة المدة", "لمدة محدودة", "محدد المدة"]},
    "temps_partiel": {"label": "Temps partiel", "fr": ["temps partiel"], "ar": ["التوقيت الجزئي"]},
    "periode_essai": {"label": "Période d'essai", "fr": ["période d'essai"], "ar": ["المدة التجريبية", "فترة التجربة"]},
    "duree_travail": {"label": "Durée légale du travail", "fr": ["durée légale", "heures par semaine", "amplitude journalière"], "ar": ["المدة القانونية للعمل"]},
    "heures_sup": {"label": "Heures supplémentaires", "fr": ["heures supplémentaires"], "ar": ["الساعات الإضافية", "الساعات الاضافية"]},
    "travail_nuit": {"label": "Travail de nuit", "fr": ["travail de nuit"], "ar": ["العمل الليلي"]},
    "repos": {"label": "Repos hebdomadaire et jours fériés", "fr": ["repos hebdomadaire", "jours fériés", "journée entière de repos"], "ar": ["الراحة الأسبوعية", "الراحة الاسبوعية", "أيام العطل"]},
    "conge": {"label": "Congé annuel et absences", "fr": ["congé annuel", "congé rémunéré", "absence"], "ar": ["العطلة السنوية", "عطلة", "الغياب"]},
    "salaire": {"label": "Salaire et rémunération", "fr": ["salaire", "rémunération", "salaire national minimum"], "ar": ["الأجر", "الاجر", "المرتب"]},
    "licenciement": {"label": "Licenciement", "fr": ["licenciement", "faute grave", "compression d'effectifs"], "ar": ["التسريح", "الخطأ الجسيم", "تقليص عدد المستخدمين"]},
    "preavis": {"label": "Préavis / délai-congé", "fr": ["préavis", "délai-congé"], "ar": ["مهلة العطلة", "الإشعار المسبق", "الاشعار المسبق"]},
    "demission": {"label": "Démission", "fr": ["démission"], "ar": ["الاستقالة"]},
    "reglement_interieur": {"label": "Règlement intérieur", "fr": ["règlement intérieur"], "ar": ["النظام الداخلي"]},
    "hygiene_securite": {"label": "Hygiène, sécurité et médecine du travail", "fr": ["hygiène", "sécurité", "médecine du travail"], "ar": ["الوقاية الصحية", "الأمن", "طب العمل"]},
    "participation": {"label": "Participation des travailleurs", "fr": ["délégués du personnel", "comité de participation"], "ar": ["مندوبي المستخدمين", "لجنة المشاركة"]},
    "negociation_collective": {"label": "Conventions et accords collectifs", "fr": ["convention collective", "conventions collectives", "accord collectif", "accords collectifs"], "ar": ["الاتفاقيات الجماعية", "الاتفاقية الجماعية"]},
    "conflits": {"label": "Conflits du travail et grève", "fr": ["conflit", "grève"], "ar": ["النزاع", "الإضراب", "الاضراب"]},
    "inspection": {"label": "Inspection du travail", "fr": ["inspecteur du travail", "inspection du travail"], "ar": ["مفتش العمل", "مفتشية العمل"]},
    "mineurs_apprentissage": {"label": "Âge minimum, mineurs, apprentissage", "fr": ["âge minimum", "mineur", "apprentissage"], "ar": ["القاصر", "التمهين"]},
    "sanctions": {"label": "Sanctions pénales (amendes)", "fr": ["amende", "puni"], "ar": ["غرامة", "يعاقب"]},
}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "ى": "ي"}))


def concepts_of(text: str) -> list[str]:
    """Concepts repérés dans un texte d'article (FR ou AR) par mots-clés."""
    t = _fold(text)
    found = []
    for key, c in CONCEPTS.items():
        if any(_fold(k) in t for k in c["fr"] + c["ar"]):
            found.append(key)
    return found


def article_node(text_ref: str, no: str) -> str:
    return f"{text_ref}#art.{no}"


def parse_ref(ref: str) -> tuple[str, str]:
    """'ordonnance:96-21' -> ('ordonnance', '96-21')."""
    t, _, n = ref.partition(":")
    return t, n


def sort_key_article(no: str):
    m = re.match(r"(\d+)(?:-(\d+))?\s*(bis|ter|quater)?", no)
    if not m:
        return (9999, 0, 0)
    return (int(m.group(1)), int(m.group(2) or 0), {"": 0, "bis": 1, "ter": 2, "quater": 3}[m.group(3) or ""])
