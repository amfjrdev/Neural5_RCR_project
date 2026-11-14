"""Évaluation chiffrée du filtre sur un échantillon annoté à la main.

1. sample_for_annotation : tire un échantillon stratifié (moitié prédits « keep/review »,
   moitié prédits « reject ») et l'écrit en CSV avec une colonne gold vide ;
2. l'équipe remplit gold (keep / reject) en lisant chaque texte ;
3. evaluate_filter : relit le CSV, enregistre les annotations en base et calcule
   précision, rappel, F1, exactitude + la liste des erreurs.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

FIELDS = ["text_id", "year", "number", "edition", "seq", "text_type", "text_number",
          "title", "predicted", "score", "gold", "annotateur", "remarque"]


def sample_for_annotation(conn, out_csv: Path, n: int = 20, seed: int = 42) -> int:
    rows = conn.execute(
        """SELECT t.id, i.year, i.number, i.edition, t.seq, t.text_type, t.text_number, t.title,
                  t.relevance, t.relevance_score FROM texts t JOIN issues i ON i.id = t.issue_id""").fetchall()
    rng = random.Random(seed)
    pos = [r for r in rows if r["relevance"] in ("keep", "review")]
    neg = [r for r in rows if r["relevance"] == "reject"]
    k_pos = min(len(pos), n // 2)
    k_neg = min(len(neg), n - k_pos)
    k_pos = min(len(pos), n - k_neg)
    picked = rng.sample(pos, k_pos) + rng.sample(neg, k_neg)
    rng.shuffle(picked)  # l'annotateur ne doit pas deviner la prédiction par l'ordre
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in picked:
            w.writerow({"text_id": r["id"], "year": r["year"], "number": r["number"],
                        "edition": r["edition"], "seq": r["seq"], "text_type": r["text_type"],
                        "text_number": r["text_number"] or "", "title": r["title"][:300],
                        "predicted": r["relevance"], "score": r["relevance_score"],
                        "gold": "", "annotateur": "", "remarque": ""})
    return len(picked)


def evaluate_filter(conn, csv_path: Path, review_as: str = "keep") -> dict:
    tp = fp = fn = tn = 0
    errors = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gold = (r["gold"] or "").strip().lower()
            if gold not in ("keep", "reject"):
                continue
            conn.execute("UPDATE texts SET gold_label=? WHERE id=?", (gold, int(r["text_id"])))
            pred = r["predicted"] if r["predicted"] != "review" else review_as
            if pred == "keep" and gold == "keep":
                tp += 1
            elif pred == "keep" and gold == "reject":
                fp += 1
                errors.append(("faux positif", r))
            elif pred == "reject" and gold == "keep":
                fn += 1
                errors.append(("faux négatif", r))
            else:
                tn += 1
    conn.commit()
    n = tp + fp + fn + tn
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"n": n, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec,
            "f1": f1, "accuracy": (tp + tn) / n if n else 0.0, "errors": errors, "review_as": review_as}


def write_report(res: dict, out_md: Path) -> None:
    lines = [
        "# Évaluation du filtre « droit du travail »", "",
        f"Échantillon annoté : **{res['n']} textes** (prédiction « review » comptée comme « {res['review_as']} »).", "",
        "| | Gold keep | Gold reject |", "|---|---|---|",
        f"| **Prédit keep** | {res['tp']} (VP) | {res['fp']} (FP) |",
        f"| **Prédit reject** | {res['fn']} (FN) | {res['tn']} (VN) |", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Précision | {res['precision']:.2f} |", f"| Rappel | {res['recall']:.2f} |",
        f"| F1 | {res['f1']:.2f} |", f"| Exactitude | {res['accuracy']:.2f} |", "",
        "Le rappel compte le plus ici : un texte du travail écarté à tort n'existera jamais pour l'assistant.", "",
        "## Erreurs à analyser", "",
    ]
    if not res["errors"]:
        lines.append("Aucune erreur sur cet échantillon.")
    for kind, r in res["errors"]:
        lines.append(f"- **{kind}** — JO {r['year']} n°{r['number']} ({r['edition']}), texte {r['seq']} "
                     f"[score {r['score']}] : {r['title'][:160]}" + (f" — *{r['remarque']}*" if r["remarque"] else ""))
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
