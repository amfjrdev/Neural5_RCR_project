"""Liste des numéros du JO à collecter.

Source principale : l'index CSV Upgrowth (CC BY 4.0), colonnes
year, issue, edition_fr, edition_ar, url_fr, url_ar, year_fully_probed.
Si l'index n'est pas disponible, on reconstruit l'URL à partir du motif officiel
(l'existence du fichier n'est alors PAS garantie).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class IssueRef:
    year: int
    number: int
    edition: str  # 'fr' | 'ar'
    url: str


def pattern_url(cfg: dict, year: int, number: int, edition: str) -> str:
    tpl = cfg["collect"]["url_fr" if edition == "fr" else "url_ar"]
    return tpl.format(year=year, num3=f"{number:03d}")


def load_index_csv(path_or_text: str | Path) -> dict[tuple[int, int, str], str]:
    """Retourne {(année, numéro, édition): url} pour les éditions marquées existantes."""
    p = Path(str(path_or_text))
    text = p.read_text(encoding="utf-8") if p.exists() else str(path_or_text)
    out: dict[tuple[int, int, str], str] = {}
    for row in csv.DictReader(io.StringIO(text)):
        y, n = int(row["year"]), int(row["issue"])
        if row.get("edition_fr") == "1" and row.get("url_fr"):
            out[(y, n, "fr")] = row["url_fr"]
        if row.get("edition_ar") == "1" and row.get("url_ar"):
            out[(y, n, "ar")] = row["url_ar"]
    return out


def issues_from_targets(cfg: dict, targets_path: Path, index: dict | None,
                        include_sample: bool = True) -> list[IssueRef]:
    data = yaml.safe_load(Path(targets_path).read_text(encoding="utf-8"))
    wanted: list[tuple[int, int, str]] = []
    for t in data.get("targets", []):
        for ed in t.get("editions", ["fr"]):
            wanted.append((t["year"], t["number"], ed))
    if include_sample:
        for s in data.get("sample_recent", []) or []:
            for n in s["numbers"]:
                for ed in s.get("editions", ["fr"]):
                    wanted.append((s["year"], n, ed))
    return resolve(cfg, wanted, index)


def resolve(cfg: dict, wanted, index: dict | None) -> list[IssueRef]:
    refs, seen = [], set()
    for y, n, ed in wanted:
        if (y, n, ed) in seen:
            continue
        seen.add((y, n, ed))
        if index is not None:
            url = index.get((y, n, ed))
            if url is None:
                print(f"  [index] {ed.upper()} {y} n°{n} absent de l'index : ignoré")
                continue
        else:
            url = pattern_url(cfg, y, n, ed)
        refs.append(IssueRef(y, n, ed, url))
    return refs
