"""Chargement de la configuration (config/config.yaml) et des secrets (.env)."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Mini-lecteur .env (évite une dépendance). Ne remplace pas une variable déjà définie."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def load_config(path: str | os.PathLike | None = None) -> dict:
    _load_dotenv(ROOT / ".env")
    if path is None:
        path = ROOT / "config" / "config.yaml"
        if not Path(path).exists():  # premier lancement : on retombe sur l'exemple
            path = ROOT / "config" / "config.example.yaml"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    data_dir = Path(cfg["paths"]["data_dir"])
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    cfg["paths"]["data_dir"] = data_dir
    for sub in ("raw/fr", "raw/ar", "text", "llm_cache"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    cfg["paths"]["db"] = data_dir / "jurideazor.sqlite"
    return cfg
