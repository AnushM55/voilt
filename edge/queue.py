"""SQLite-backed durable queue for edge event upload."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from shared.schemas import ViolationEvent


@dataclass
class QueueItem:
    """Leased queue item returned to uploader."""

    id: int
    event: ViolationEvent
    attempts: int


class SQLiteEventQueue:
    """Durable queue with lease/ack semantics and retries."""

    def __init__(self, db_path: str) -> None:
        path = Path(db_path)
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS event_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_json TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                leased_until TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def enqueue(self, event: ViolationEvent) -> int:
        cursor = self._conn.execute(
            "INSERT INTO event_queue (event_json, created_at) VALUES (?, ?)",
            (event.model_dump_json(), datetime.now(UTC).isoformat()),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def lease(self, limit: int = 1, lease_seconds: int = 30) -> list[QueueItem]:
        now = datetime.now(UTC)
        lease_until = datetime.fromtimestamp(now.timestamp() + lease_seconds, UTC).isoformat()
        rows = self._conn.execute(
            """
            SELECT id, event_json, attempts
            FROM event_queue
            WHERE leased_until IS NULL OR leased_until < ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (now.isoformat(), limit),
        ).fetchall()
        items: list[QueueItem] = []
        for row in rows:
            self._conn.execute(
                "UPDATE event_queue SET leased_until = ?, attempts = attempts + 1 WHERE id = ?",
                (lease_until, row["id"]),
            )
            payload = json.loads(row["event_json"])
            items.append(
                QueueItem(
                    id=int(row["id"]),
                    event=ViolationEvent.model_validate(payload),
                    attempts=int(row["attempts"]) + 1,
                )
            )
        self._conn.commit()
        return items

    def ack(self, item_id: int) -> None:
        self._conn.execute("DELETE FROM event_queue WHERE id = ?", (item_id,))
        self._conn.commit()

    def size(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as count FROM event_queue").fetchone()
        if row is None:
            return 0
        return int(row["count"])
