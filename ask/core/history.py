import sqlite3
from pathlib import Path
import os

DB_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "ask-cli"
DB_FILE = DB_DIR / "history.sqlite3"


class History:
    def __init__(self):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL
                )
            """)

    def _connect(self):
        return sqlite3.connect(DB_FILE)

    def add(self, prompt, response, provider, model):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversations (prompt, response, provider, model) VALUES (?, ?, ?, ?)",
                (prompt, response, provider, model),
            )

    def recent(self, limit=20):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(row) for row in rows]
