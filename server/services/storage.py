"""Persistence abstractions for raw and verified events."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.schemas import VerifiedEvent, ViolationEvent


@dataclass
class InMemoryStore:
    """Simple in-memory persistence for tests and early development."""

    raw_events: list[ViolationEvent]
    verified_events: list[VerifiedEvent]
    idempotency_index: dict[str, str]
    upload_dir: Path

    def __init__(self, upload_dir: str = "server/uploads") -> None:
        self.raw_events = []
        self.verified_events = []
        self.idempotency_index = {}
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def store_raw(self, event: ViolationEvent) -> bool:
        existing_event_id = self.idempotency_index.get(event.idempotency_key)
        if existing_event_id is not None:
            return False
        self.raw_events.append(event)
        self.idempotency_index[event.idempotency_key] = str(event.event_id)
        return True

    def store_verified(self, event: VerifiedEvent) -> None:
        self.verified_events.append(event)

    def save_evidence(self, event_id: str, filename: str, content: bytes) -> str:
        event_dir = self.upload_dir / event_id
        event_dir.mkdir(parents=True, exist_ok=True)
        target = event_dir / filename
        target.write_bytes(content)
        return str(target)
