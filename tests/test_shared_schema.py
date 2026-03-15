from datetime import UTC, datetime

import pytest

from shared.schemas import BBox, EventLocation, LocationSource, ViolationEvent, ViolationType


def test_bbox_validation_rejects_invalid_points() -> None:
    with pytest.raises(ValueError):
        BBox(x1=0.2, y1=0.2, x2=0.1, y2=0.3)


def test_violation_event_validates_required_fields() -> None:
    event = ViolationEvent(
        idempotency_key="abcde12345fgh",
        device_id="pi-1",
        track_id="t-1",
        captured_at=datetime.now(UTC),
        violations=[ViolationType.NO_HELMET],
        max_confidence=0.9,
        motorcycle_bbox=BBox(x1=1, y1=1, x2=10, y2=10),
        location=EventLocation(lat=12.0, lon=77.0, accuracy_m=120.0, source=LocationSource.WIFI),
        model_version="model-v1",
        software_version="0.1.0",
    )
    assert event.device_id == "pi-1"
