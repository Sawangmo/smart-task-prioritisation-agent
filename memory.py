
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "task_memory.db"


def _connect():
    """Connect to the SQLite database and create required tables."""
    connection = sqlite3.connect(DB_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            tasks_json TEXT NOT NULL,
            available_hours REAL NOT NULL,
            feedback TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS timetable_progress (
            session_id TEXT PRIMARY KEY,
            completed INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    connection.commit()
    return connection


def save_session(
    tasks: list[dict],
    available_hours: float,
    feedback: str = "",
) -> None:
    """Save an agent planning session."""
    connection = _connect()

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO sessions (
                    created_at,
                    tasks_json,
                    available_hours,
                    feedback
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    json.dumps(tasks),
                    float(available_hours),
                    feedback.strip(),
                ),
            )
    finally:
        connection.close()


def get_recent_sessions(limit: int = 5) -> list[dict]:
    """Return recent planning sessions."""
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                created_at,
                tasks_json,
                available_hours,
                feedback
            FROM sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
    finally:
        connection.close()

    return [
        {
            "created_at": created_at,
            "tasks": json.loads(tasks_json),
            "available_hours": hours,
            "feedback": feedback,
        }
        for created_at, tasks_json, hours, feedback in rows
    ]


def set_timetable_completion(
    session_id: str,
    completed: bool,
) -> None:
    """Save or update a timetable session's completion status."""
    connection = _connect()

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO timetable_progress (
                    session_id,
                    completed,
                    updated_at
                )
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    completed = excluded.completed,
                    updated_at = excluded.updated_at
                """,
                (
                    str(session_id),
                    int(completed),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
    finally:
        connection.close()


def get_timetable_progress() -> dict[str, bool]:
    """Return saved completion statuses indexed by session ID."""
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT session_id, completed
            FROM timetable_progress
            """
        ).fetchall()
    finally:
        connection.close()

    return {
        session_id: bool(completed)
        for session_id, completed in rows
    }
