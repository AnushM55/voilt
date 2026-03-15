from pathlib import Path

from edge.queue import SQLiteEventQueue
from shared.schemas import (
    BBox,
    EventLocation,
    LocationSource,
    ViolationEvent,
    ViolationType,
)


def _sample_event() -> ViolationEvent:
    return ViolationEvent(
        idempotency_key="1234567890ab",
        device_id="pi-1",
        track_id="track-1",
        violations=[ViolationType.NO_HELMET],
        max_confidence=0.8,
        motorcycle_bbox=BBox(x1=1, y1=1, x2=20, y2=20),
        location=EventLocation(lat=12.0, lon=77.0, accuracy_m=90.0, source=LocationSource.IP),
        model_version="m1",
        software_version="s1",
    )


def test_sqlite_queue_enqueue_lease_ack(tmp_path: Path) -> None:
    db_path = tmp_path / "queue.db"
    queue = SQLiteEventQueue(str(db_path))
    inserted_id = queue.enqueue(_sample_event())
    assert inserted_id > 0
    assert queue.size() == 1

    leased = queue.lease(limit=1)
    assert len(leased) == 1
    assert leased[0].event.device_id == "pi-1"

    queue.ack(leased[0].id)
    assert queue.size() == 0
