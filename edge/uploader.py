"""HTTP uploader for edge events with retry-safe semantics."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import httpx

from edge.queue import QueueItem, SQLiteEventQueue


class EventUploader:
    """Leases queued items and posts them to backend ingest endpoint."""

    def __init__(self, ingest_url: str, timeout_seconds: float = 5.0) -> None:
        self._ingest_url = ingest_url
        self._timeout_seconds = timeout_seconds

    def upload_once(self, queue: SQLiteEventQueue, batch_size: int = 10) -> tuple[int, int]:
        leased = queue.lease(limit=batch_size)
        sent = 0
        failed = 0
        if not leased:
            return sent, failed
        with httpx.Client(timeout=self._timeout_seconds) as client:
            for item in leased:
                if self._send_item(client, item):
                    queue.ack(item.id)
                    sent += 1
                else:
                    failed += 1
        return sent, failed

    def _send_item(self, client: httpx.Client, item: QueueItem) -> bool:
        files: list[tuple[str, tuple[str, bytes, str]]] = []
        opened_handles: list[BinaryIO] = []
        try:
            for index, evidence in enumerate(item.event.evidence):
                evidence_path = Path(evidence.uri)
                if not evidence_path.exists() or not evidence_path.is_file():
                    continue
                handle = evidence_path.open("rb")
                opened_handles.append(handle)
                files.append(
                    (
                        f"evidence_{index}",
                        (evidence_path.name, handle.read(), "image/jpeg"),
                    )
                )
            response = client.post(
                self._ingest_url,
                data={"event_json": item.event.model_dump_json()},
                files=files,
                headers={"X-Idempotency-Key": item.event.idempotency_key},
            )
        except httpx.HTTPError:
            return False
        finally:
            for handle in opened_handles:
                handle.close()
        return 200 <= response.status_code < 300
