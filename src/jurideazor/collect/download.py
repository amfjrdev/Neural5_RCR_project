"""Téléchargement poli et rejouable des PDF du Journal officiel.

- vérifie robots.txt avant toute requête (et s'arrête si on ne peut pas le lire) ;
- une pause minimale entre deux requêtes (Crawl-delay respecté s'il est plus grand) ;
- reprise : un PDF déjà présent avec le même SHA-256 n'est pas retéléchargé ;
- chaque fichier garde son URL source (table issues) et son empreinte (downloads).
"""
from __future__ import annotations

import hashlib
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from ..db import upsert_issue
from .index import IssueRef


class RobotsGuard:
    def __init__(self, session: requests.Session, user_agent: str, respect: bool = True):
        self.session, self.ua, self.respect = session, user_agent, respect
        self._parsers: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.report: dict[str, str] = {}

    def _parser(self, url: str):
        host = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if host not in self._parsers:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.session.get(host + "/robots.txt", timeout=30)
                if r.status_code == 200:
                    rp.parse(r.text.splitlines())
                    self.report[host] = r.text
                elif r.status_code in (404, 410):
                    rp.parse([])  # pas de robots.txt = pas de restriction déclarée
                    self.report[host] = f"(aucun robots.txt : HTTP {r.status_code})"
                else:
                    rp = None
                    self.report[host] = f"(robots.txt illisible : HTTP {r.status_code})"
            except requests.RequestException as e:
                rp = None
                self.report[host] = f"(robots.txt injoignable : {e.__class__.__name__})"
            self._parsers[host] = rp
        return self._parsers[host]

    def allowed(self, url: str) -> bool:
        if not self.respect:
            return True
        rp = self._parser(url)
        return bool(rp and rp.can_fetch(self.ua, url))

    def crawl_delay(self, url: str) -> float:
        rp = self._parser(url)
        d = rp.crawl_delay(self.ua) if rp else None
        return float(d) if d else 0.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path_for(data_dir: Path, ref: IssueRef) -> Path:
    prefix = "F" if ref.edition == "fr" else "A"
    return data_dir / "raw" / ref.edition / str(ref.year) / f"{prefix}{ref.year}{ref.number:03d}.pdf"


def download_issues(conn, cfg: dict, refs: list[IssueRef], dry_run: bool = False) -> dict:
    c = cfg["collect"]
    data_dir: Path = cfg["paths"]["data_dir"]
    s = requests.Session()
    s.headers["User-Agent"] = cfg["project"]["user_agent"]
    guard = RobotsGuard(s, cfg["project"]["user_agent"], c.get("respect_robots", True))
    stats = {"ok": 0, "skipped": 0, "blocked": 0, "failed": 0}
    last_request = 0.0

    for ref in refs:
        issue_id = upsert_issue(conn, ref.year, ref.number, ref.edition, ref.url)
        dest = local_path_for(data_dir, ref)
        prev = conn.execute("SELECT sha256 FROM downloads WHERE issue_id=?", (issue_id,)).fetchone()
        if dest.exists() and prev and prev["sha256"] == sha256_file(dest):
            stats["skipped"] += 1
            continue
        if not guard.allowed(ref.url):
            print(f"  [robots] refusé ou robots.txt non vérifiable : {ref.url}")
            stats["blocked"] += 1
            continue
        if dry_run:
            print(f"  [dry-run] {ref.url} -> {dest}")
            continue

        wait = max(c["delay_seconds"], guard.crawl_delay(ref.url)) - (time.time() - last_request)
        if wait > 0:
            time.sleep(wait)

        status, err = None, None
        for attempt in range(1, c["max_retries"] + 1):
            last_request = time.time()
            try:
                r = s.get(ref.url, timeout=c["timeout"], stream=True)
                status = r.status_code
                if r.status_code == 200:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dest.with_suffix(".part")
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(1 << 16):
                            f.write(chunk)
                    with open(tmp, "rb") as f:
                        if f.read(5) != b"%PDF-":
                            tmp.unlink()
                            raise ValueError("la réponse n'est pas un PDF")
                    tmp.replace(dest)
                    err = None
                    break
                err = f"HTTP {r.status_code}"
                if r.status_code in (403, 404, 410):
                    break  # inutile d'insister
            except (requests.RequestException, ValueError) as e:
                err = f"{e.__class__.__name__}: {e}"
            time.sleep(c["delay_seconds"] * attempt)  # backoff

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if err is None:
            digest = sha256_file(dest)
            conn.execute(
                """INSERT INTO downloads (issue_id, local_path, sha256, bytes, http_status, fetched_at, error)
                   VALUES (?,?,?,?,?,?,NULL)
                   ON CONFLICT (issue_id) DO UPDATE SET local_path=excluded.local_path,
                     sha256=excluded.sha256, bytes=excluded.bytes, http_status=excluded.http_status,
                     fetched_at=excluded.fetched_at, error=NULL""",
                (issue_id, str(dest), digest, dest.stat().st_size, status, now),
            )
            stats["ok"] += 1
            print(f"  [ok] {ref.edition.upper()} {ref.year} n°{ref.number} ({dest.stat().st_size // 1024} Ko)")
        else:
            conn.execute(
                """INSERT INTO downloads (issue_id, http_status, fetched_at, error) VALUES (?,?,?,?)
                   ON CONFLICT (issue_id) DO UPDATE SET http_status=excluded.http_status,
                     fetched_at=excluded.fetched_at, error=excluded.error""",
                (issue_id, status, now, err),
            )
            stats["failed"] += 1
            print(f"  [échec] {ref.url} : {err}")
        conn.commit()

    stats["robots"] = guard.report
    return stats


def import_local_pdf(conn, cfg: dict, pdf: Path, year: int, number: int, edition: str,
                     url: str | None = None, origin: str = "import_local") -> int:
    """Enregistre un PDF obtenu hors script (téléchargé à la main, corpus de dépannage).
    Le lien source officiel reste obligatoire : on le reconstruit si absent."""
    from .index import pattern_url
    import shutil

    url = url or pattern_url(cfg, year, number, edition)
    ref = IssueRef(year, number, edition, url)
    issue_id = upsert_issue(conn, year, number, edition, url, origin)
    dest = local_path_for(cfg["paths"]["data_dir"], ref)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if Path(pdf).resolve() != dest.resolve():
        shutil.copyfile(pdf, dest)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """INSERT INTO downloads (issue_id, local_path, sha256, bytes, http_status, fetched_at, error)
           VALUES (?,?,?,?,NULL,?,NULL)
           ON CONFLICT (issue_id) DO UPDATE SET local_path=excluded.local_path, sha256=excluded.sha256,
             bytes=excluded.bytes, fetched_at=excluded.fetched_at, error=NULL""",
        (issue_id, str(dest), sha256_file(dest), dest.stat().st_size, now),
    )
    conn.commit()
    return issue_id
