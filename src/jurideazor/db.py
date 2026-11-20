"""Schéma SQLite de la base de connaissances.

Semaine 1 : issues, downloads, pages, texts sont remplies.
articles, article_versions, relations sont créées dès maintenant pour fixer le
modèle de données (structuration et versions : semaines suivantes).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;

-- Un numéro du Journal officiel dans une édition (fr / ar)
CREATE TABLE IF NOT EXISTS issues (
    id          INTEGER PRIMARY KEY,
    year        INTEGER NOT NULL,
    number      INTEGER NOT NULL,
    edition     TEXT    NOT NULL CHECK (edition IN ('fr', 'ar')),
    url         TEXT    NOT NULL,           -- lien source officiel
    origin      TEXT    NOT NULL DEFAULT 'joradp',  -- joradp | import_local | corpus_depannage
    UNIQUE (year, number, edition)
);

-- Résultat du téléchargement (une ligne par issue, rejouable sans doublon)
CREATE TABLE IF NOT EXISTS downloads (
    issue_id    INTEGER PRIMARY KEY REFERENCES issues(id) ON DELETE CASCADE,
    local_path  TEXT,
    sha256      TEXT,
    bytes       INTEGER,
    http_status INTEGER,
    fetched_at  TEXT,
    error       TEXT
);

-- Traçabilité de l'extraction page par page (texte natif ou OCR)
CREATE TABLE IF NOT EXISTS pages (
    issue_id    INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    page_no     INTEGER NOT NULL,
    method      TEXT    NOT NULL CHECK (method IN ('text', 'ocr', 'empty')),
    chars       INTEGER NOT NULL,
    PRIMARY KEY (issue_id, page_no)
);

-- Un texte juridique isolé dans un numéro (loi, décret, arrêté...)
CREATE TABLE IF NOT EXISTS texts (
    id                INTEGER PRIMARY KEY,
    issue_id          INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    seq               INTEGER NOT NULL,         -- ordre dans le numéro
    lang              TEXT    NOT NULL,
    text_type         TEXT,                     -- loi, ordonnance, decret_executif, arrete...
    text_number       TEXT,                     -- ex. 90-11, 90-02 (forme canonique AA-NN)
    sign_date         TEXT,                     -- date de signature (ISO, grégorienne)
    norm_rank         INTEGER,                  -- hiérarchie des normes : 1 = Constitution
    title             TEXT    NOT NULL,
    section           TEXT,                     -- rubrique / ministère émetteur
    page_start        INTEGER,
    page_end          INTEGER,
    body              TEXT    NOT NULL,
    content_sha256    TEXT    NOT NULL,
    extraction_method TEXT,                     -- text | ocr | mixed
    relevance         TEXT,                     -- keep | review | reject
    relevance_score   REAL,
    relevance_reasons TEXT,
    is_circular       INTEGER NOT NULL DEFAULT 0,  -- 1 = « interprétation de l'administration »
    gold_label        TEXT,                     -- annotation manuelle (keep / reject)
    source_url        TEXT    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (issue_id, seq)
);
CREATE INDEX IF NOT EXISTS idx_texts_ref ON texts (text_type, text_number);
CREATE INDEX IF NOT EXISTS idx_texts_rel ON texts (relevance);

-- ===== Semaines suivantes : structuration, versions, liens =====
CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY,
    text_ref     TEXT    NOT NULL,       -- ex. 'loi:90-11' (identité stable, indépendante du numéro de JO)
    article_no   TEXT    NOT NULL,       -- '33', '12 bis', '1er'
    parent_path  TEXT,                   -- 'Titre II > Chapitre I > Section 2'
    UNIQUE (text_ref, article_no)
);

CREATE TABLE IF NOT EXISTS article_versions (
    id               INTEGER PRIMARY KEY,
    article_id       INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    lang             TEXT    NOT NULL,
    content          TEXT    NOT NULL,
    valid_from       TEXT,               -- entrée en vigueur de cette version
    valid_to         TEXT,               -- NULL = toujours en vigueur
    status           TEXT    NOT NULL CHECK (status IN ('en_vigueur', 'remplacee', 'abrogee')),
    source_text_id   INTEGER REFERENCES texts(id),  -- texte qui a introduit cette version
    UNIQUE (article_id, lang, valid_from)
);

CREATE TABLE IF NOT EXISTS relations (
    id              INTEGER PRIMARY KEY,
    src_text_id     INTEGER NOT NULL REFERENCES texts(id) ON DELETE CASCADE,
    relation        TEXT    NOT NULL CHECK (relation IN ('modifie', 'complete', 'abroge', 'applique', 'vise')),
    target_text_ref TEXT    NOT NULL,    -- ex. 'loi:90-11'
    target_article  TEXT,                -- NULL = texte entier
    UNIQUE (src_text_id, relation, target_text_ref, target_article)
);
"""

# Hiérarchie des normes (règle d'or du projet : le rang supérieur l'emporte)
NORM_RANK = {
    "constitution": 1,
    "loi_organique": 2, "loi": 2, "ordonnance": 2, "decret_legislatif": 2,
    "decret_presidentiel": 3, "decret_executif": 3, "decret": 3,
    "arrete_interministeriel": 4, "arrete": 4, "decision": 4,
    "circulaire": 5, "instruction": 5,
    "avis": 6, "proclamation": 6, "deliberation": 6,
}


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> sqlite3.Connection:
    conn = connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def upsert_issue(conn, year: int, number: int, edition: str, url: str, origin: str = "joradp") -> int:
    conn.execute(
        """INSERT INTO issues (year, number, edition, url, origin) VALUES (?,?,?,?,?)
           ON CONFLICT (year, number, edition) DO UPDATE SET url = excluded.url""",
        (year, number, edition, url, origin),
    )
    row = conn.execute(
        "SELECT id FROM issues WHERE year=? AND number=? AND edition=?", (year, number, edition)
    ).fetchone()
    return row["id"]
