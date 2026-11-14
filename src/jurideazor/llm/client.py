"""Client du modèle de langage commun, avec cache disque et compteur d'appels.

Règles du module appliquées ici :
- un seul modèle, imposé par l'enseignant (provider + model dans config.yaml) ;
- toutes les réponses sont mises en cache : le jeu de test se rejoue sans appel ;
- le nombre d'appels réels est compté (à reporter dans le rapport) ;
- la clé est lue dans l'environnement (.env ignoré par Git), jamais en dur ;
- n'envoyer QUE des textes publics (lois, décrets...), jamais de données personnelles.

Semaine 1 : uniquement un appel de test (cli llm-ping). Le modèle servira à partir
de la structuration (cas difficiles) et surtout pour les réponses.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import requests


class LLMClient:
    def __init__(self, cfg: dict):
        l = cfg["llm"]
        self.provider, self.model = l["provider"], l["model"]
        self.temperature = l.get("temperature", 0)
        if "A_CONFIRMER" in (self.provider, self.model):
            raise RuntimeError("Renseignez llm.provider et llm.model (annoncés par l'enseignant) dans config/config.yaml")
        self.cache_dir: Path = cfg["paths"]["data_dir"] / "llm_cache"
        self.stats_file = self.cache_dir / "_stats.json"
        self.stats = json.loads(self.stats_file.read_text()) if self.stats_file.exists() else {"api_calls": 0, "cache_hits": 0}

    def _key(self, system: str, prompt: str) -> str:
        payload = json.dumps([self.provider, self.model, self.temperature, system, prompt], ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _save_stats(self):
        self.stats_file.write_text(json.dumps(self.stats, indent=2))

    def generate(self, prompt: str, system: str = "", use_cache: bool = True) -> str:
        key = self._key(system, prompt)
        path = self.cache_dir / f"{key}.json"
        if use_cache and path.exists():
            self.stats["cache_hits"] += 1
            self._save_stats()
            return json.loads(path.read_text(encoding="utf-8"))["response"]
        text = self._call(prompt, system)
        self.stats["api_calls"] += 1
        self._save_stats()
        path.write_text(json.dumps({"provider": self.provider, "model": self.model, "system": system,
                                    "prompt": prompt, "response": text, "ts": time.time()},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
        return text

    def _call(self, prompt: str, system: str) -> str:
        if self.provider == "gemini":
            key = os.environ.get("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("GEMINI_API_KEY absente (.env)")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": self.temperature}}
            if system:
                body["systemInstruction"] = {"parts": [{"text": system}]}
            r = requests.post(url, params={"key": key}, json=body, timeout=120)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        if self.provider == "groq":
            key = os.environ.get("GROQ_API_KEY")
            if not key:
                raise RuntimeError("GROQ_API_KEY absente (.env)")
            msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {key}"},
                              json={"model": self.model, "messages": msgs, "temperature": self.temperature},
                              timeout=120)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        raise ValueError(f"provider inconnu : {self.provider}")
