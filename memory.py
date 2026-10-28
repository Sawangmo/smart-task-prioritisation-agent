
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "task_memory.db"


def _connect():
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

    connection.commit()
    return connection


def save_session(
    tasks: list[dict],
    available_hours: float,
    feedback: str = ""
) -> None:
    connection = _connect()

    try:
        with connection:
            connection.execute(
                """
                INSERT INTO sessions
                (created_at, tasks_json, available_hours, feedback)
                VALUES (?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    json.dumps(tasks),
                    float(available_hours),
                    feedback.strip()
                )
            )
    finally:
        connection.close()


def get_recent_sessions(limit: int = 5) -> list[dict]:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT created_at, tasks_json,
                   available_hours, feedback
            FROM sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, int(limit)),)
        ).fetchall()
    finally:
        connection.close()

    return [
        {
            "created_at": created_at,
            "tasks": json.loads(tasks_json),
            "available_hours": hours,
            "feedback": feedback
        }
        for created_at, tasks_json, hours, feedback in rows
    ]
