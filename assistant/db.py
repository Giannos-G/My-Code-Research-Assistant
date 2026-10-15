"""SQLite storage for the research history log."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "research.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def log_research(question: str, answer: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO research_log (question, answer) VALUES (?, ?)",
            (question, answer),
        )
        return cur.lastrowid


def list_past_research(keyword: str | None = None) -> list[sqlite3.Row]:
    with _connect() as conn:
        if keyword:
            return conn.execute(
                "SELECT * FROM research_log WHERE question LIKE ? OR answer LIKE ? "
                "ORDER BY id DESC",
                (f"%{keyword}%", f"%{keyword}%"),
            ).fetchall()
        return conn.execute("SELECT * FROM research_log ORDER BY id DESC").fetchall()
