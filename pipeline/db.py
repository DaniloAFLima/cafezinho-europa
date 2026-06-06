"""Camada de acesso a SQLite (artigos e execuções)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable


class ArticleStatus(str, Enum):
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    SKIPPED = "skipped"
    FAILED = "failed"


SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    url           TEXT PRIMARY KEY,
    source        TEXT NOT NULL,
    language      TEXT NOT NULL,
    title_orig    TEXT NOT NULL,
    published_at  TIMESTAMP NOT NULL,
    fetched_at    TIMESTAMP NOT NULL,
    status        TEXT NOT NULL,
    wp_post_id    INTEGER,
    relevance     REAL,
    error_msg     TEXT
);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_fetched_at ON articles(fetched_at);

CREATE TABLE IF NOT EXISTS runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TIMESTAMP NOT NULL,
    finished_at  TIMESTAMP,
    fetched      INTEGER DEFAULT 0,
    published    INTEGER DEFAULT 0,
    skipped      INTEGER DEFAULT 0,
    failed       INTEGER DEFAULT 0,
    cost_usd     REAL DEFAULT 0.0,
    error_log    TEXT
);
"""


class Database:
    """Wrapper fino sobre SQLite com os métodos que o pipeline precisa."""

    def __init__(self, path: str | Path = "data/cafezinho.db") -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert_article(
        self,
        *,
        url: str,
        source: str,
        language: str,
        title_orig: str,
        published_at: datetime,
        status: ArticleStatus,
        relevance: float | None = None,
    ) -> None:
        # mantém a primeira ocorrência do URL (não sobrescreve status)
        self.conn.execute(
            """
            INSERT OR IGNORE INTO articles
                (url, source, language, title_orig, published_at, fetched_at, status, relevance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                source,
                language,
                title_orig,
                published_at.isoformat(),
                datetime.now(timezone.utc).isoformat(),
                status.value,
                relevance,
            ),
        )
        self.conn.commit()

    def get_article(self, url: str) -> dict | None:
        cursor = self.conn.execute("SELECT * FROM articles WHERE url = ?", (url,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def filter_new_urls(self, urls: Iterable[str]) -> list[str]:
        urls = list(urls)
        if not urls:
            return []
        placeholders = ",".join("?" * len(urls))
        cursor = self.conn.execute(
            f"SELECT url FROM articles WHERE url IN ({placeholders})", urls
        )
        ja_vistos = {row[0] for row in cursor.fetchall()}
        return [u for u in urls if u not in ja_vistos]

    def update_article_status(
        self,
        *,
        url: str,
        status: ArticleStatus,
        wp_post_id: int | None = None,
        error_msg: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE articles
            SET status = ?, wp_post_id = COALESCE(?, wp_post_id), error_msg = ?
            WHERE url = ?
            """,
            (status.value, wp_post_id, error_msg, url),
        )
        self.conn.commit()

    def start_run(self) -> int:
        cursor = self.conn.execute(
            "INSERT INTO runs (started_at) VALUES (?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
        self.conn.commit()
        return cursor.lastrowid

    def finish_run(
        self,
        run_id: int,
        *,
        fetched: int,
        published: int,
        skipped: int,
        failed: int,
        cost_usd: float,
        error_log: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE runs SET
                finished_at = ?,
                fetched = ?, published = ?, skipped = ?, failed = ?,
                cost_usd = ?, error_log = ?
            WHERE id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                fetched,
                published,
                skipped,
                failed,
                cost_usd,
                error_log,
                run_id,
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
