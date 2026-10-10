"""Хранилище: один файл SQLite в папке data/."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import PROJECT_ROOT

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "bot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    telegram_id INTEGER PRIMARY KEY,
    full_name   TEXT,
    username    TEXT,
    status      TEXT NOT NULL
                CHECK (status IN ('awaiting_name', 'pending', 'active', 'rejected', 'removed')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS groups (
    chat_id     INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL
                CHECK (status IN ('pending', 'active', 'rejected', 'removed')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

_conn: sqlite3.Connection | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db(path: Path = DEFAULT_DB_PATH) -> None:
    global _conn
    path.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(path)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")
    _conn.execute("PRAGMA journal_mode = WAL")
    _conn.executescript(SCHEMA)
    _conn.commit()


def _db() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("База не открыта: вызовите init_db()")
    return _conn


# --- Сотрудники ---

def get_employee(telegram_id: int) -> sqlite3.Row | None:
    return _db().execute(
        "SELECT * FROM employees WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()


def start_registration(telegram_id: int, username: str | None) -> None:
    """Новый или ранее отключённый человек начинает подключение."""
    now = _now()
    _db().execute(
        """
        INSERT INTO employees (telegram_id, username, status, created_at, updated_at)
        VALUES (?, ?, 'awaiting_name', ?, ?)
        ON CONFLICT (telegram_id) DO UPDATE
            SET username = excluded.username, status = 'awaiting_name', updated_at = excluded.updated_at
        """,
        (telegram_id, username, now, now),
    )
    _db().commit()


def submit_name(telegram_id: int, full_name: str) -> None:
    _db().execute(
        """
        UPDATE employees SET full_name = ?, status = 'pending', updated_at = ?
        WHERE telegram_id = ? AND status = 'awaiting_name'
        """,
        (full_name, _now(), telegram_id),
    )
    _db().commit()


def change_employee_status(telegram_id: int, expected: str, new: str) -> bool:
    """Меняет статус, только если он сейчас равен expected. False — уже кто-то поменял."""
    cur = _db().execute(
        "UPDATE employees SET status = ?, updated_at = ? WHERE telegram_id = ? AND status = ?",
        (new, _now(), telegram_id, expected),
    )
    _db().commit()
    return cur.rowcount == 1


def list_employees(*statuses: str) -> list[sqlite3.Row]:
    marks = ",".join("?" * len(statuses))
    return _db().execute(
        f"SELECT * FROM employees WHERE status IN ({marks}) ORDER BY full_name",
        statuses,
    ).fetchall()


# --- Группы ---

def get_group(chat_id: int) -> sqlite3.Row | None:
    return _db().execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,)).fetchone()


def save_group(chat_id: int, title: str, status: str) -> None:
    now = _now()
    _db().execute(
        """
        INSERT INTO groups (chat_id, title, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (chat_id) DO UPDATE
            SET title = excluded.title, status = excluded.status, updated_at = excluded.updated_at
        """,
        (chat_id, title, status, now, now),
    )
    _db().commit()


def change_group_status(chat_id: int, expected: str, new: str) -> bool:
    cur = _db().execute(
        "UPDATE groups SET status = ?, updated_at = ? WHERE chat_id = ? AND status = ?",
        (new, _now(), chat_id, expected),
    )
    _db().commit()
    return cur.rowcount == 1


def list_groups(*statuses: str) -> list[sqlite3.Row]:
    marks = ",".join("?" * len(statuses))
    return _db().execute(
        f"SELECT * FROM groups WHERE status IN ({marks}) ORDER BY title", statuses
    ).fetchall()
