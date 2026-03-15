"""Background verification worker primitives."""

from __future__ import annotations

from server.storage import InMemoryStore
from server.verification import verify_event


class VerificationWorker:
    """Processes raw events and persists verified output."""

    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    def run_once(self) -> int:
        """Process unverified raw events for current in-memory session."""

        processed = 0
        existing_ids = {item.event.event_id for item in self._store.verified_events}
        for raw_event in self._store.raw_events:
            if raw_event.event_id in existing_ids:
                continue
            self._store.store_verified(verify_event(raw_event))
            processed += 1
        return processed
