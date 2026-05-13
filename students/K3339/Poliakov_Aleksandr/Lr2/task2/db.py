from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("parsed_pages.db")


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    path = Path(db_path)
    with sqlite3.connect(path, timeout=30) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parsed_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                parser_type TEXT NOT NULL,
                parsed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def save_page(
    url: str,
    title: str,
    parser_type: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    with sqlite3.connect(Path(db_path), timeout=30) as connection:
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute(
            """
            INSERT INTO parsed_pages (url, title, parser_type)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                parser_type = excluded.parser_type,
                parsed_at = CURRENT_TIMESTAMP
            """,
            (url, title, parser_type),
        )
        connection.commit()
