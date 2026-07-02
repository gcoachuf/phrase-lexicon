"""SQLite storage for flashcards and review state."""

import os
import sqlite3
from pathlib import Path

from scheduler import initial_card_state, today

_data_dir = Path(os.environ.get("DATA_DIR", Path(__file__).parent))
_data_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _data_dir / "cards.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english TEXT NOT NULL,
                german TEXT NOT NULL,
                deck TEXT NOT NULL,
                source TEXT NOT NULL,
                interval INTEGER NOT NULL DEFAULT 0,
                ease REAL NOT NULL DEFAULT 2.5,
                due TEXT NOT NULL,
                reps INTEGER NOT NULL DEFAULT 0,
                lapses INTEGER NOT NULL DEFAULT 0,
                UNIQUE(english, german, deck)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )


def get_meta(key: str) -> str | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(key: str, value: str) -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def import_cards(cards: list[dict]) -> tuple[int, int]:
    """Insert new cards. Returns (added, total)."""
    init_db()
    added = 0
    with connect() as conn:
        for card in cards:
            state = initial_card_state()
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO cards
                    (english, german, deck, source, interval, ease, due, reps, lapses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card["english"],
                    card["german"],
                    card["deck"],
                    card["source"],
                    state["interval"],
                    state["ease"],
                    state["due"],
                    state["reps"],
                    state["lapses"],
                ),
            )
            if cursor.rowcount:
                added += 1
        total = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    return added, total


def get_card_by_id(card_id: int, direction: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if not row:
        return None
    return _row_to_card(row, direction)


def get_due_card(direction: str) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM cards
            WHERE due <= ?
            ORDER BY due ASC, reps ASC, id ASC
            LIMIT 1
            """,
            (today().isoformat(),),
        ).fetchone()
    if not row:
        return None
    return _row_to_card(row, direction)


def get_stats() -> dict:
    init_db()
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        due = conn.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= ?", (today().isoformat(),)
        ).fetchone()[0]
        new_today = conn.execute(
            "SELECT COUNT(*) FROM cards WHERE reps = 0"
        ).fetchone()[0]
    return {"total": total, "due": due, "new": new_today}


def reset_all_progress() -> int:
    """Reset scheduling on all cards. Returns number of cards affected."""
    init_db()
    state = initial_card_state()
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE cards
            SET interval = ?, ease = ?, due = ?, reps = ?, lapses = ?
            """,
            (
                state["interval"],
                state["ease"],
                state["due"],
                state["reps"],
                state["lapses"],
            ),
        )
        return cursor.rowcount


def update_card(card_id: int, fields: dict) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE cards
            SET interval = ?, ease = ?, due = ?, reps = ?, lapses = ?
            WHERE id = ?
            """,
            (
                fields["interval"],
                fields["ease"],
                fields["due"],
                fields["reps"],
                fields["lapses"],
                card_id,
            ),
        )


def _row_to_card(row: sqlite3.Row, direction: str) -> dict:
    english = row["english"]
    german = row["german"]
    if direction == "de_en":
        front, back = german, english
    else:
        front, back = english, german

    return {
        "id": row["id"],
        "front": front,
        "back": back,
        "deck": row["deck"],
        "direction": direction,
        "interval": row["interval"],
        "ease": row["ease"],
        "due": row["due"],
        "reps": row["reps"],
        "lapses": row["lapses"],
    }
