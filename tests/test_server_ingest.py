from fastapi.testclient import TestClient

from server.app import app
from shared.schemas import (
    BBox,
    EventLocation,
    LocationSource,
    ViolationEvent,
    ViolationType,
)


def _payload() -> ViolationEvent:
    return ViolationEvent(
        idempotency_key="server-key-001",
        device_id="pi-1",
        track_id="t-1",
        violations=[ViolationType.NO_HELMET],
        max_confidence=0.9,
        motorcycle_bbox=BBox(x1=1, y1=1, x2=11, y2=11),
        location=EventLocation(lat=12.0, lon=77.0, accuracy_m=100, source=LocationSource.IP),
        model_version="m1",
        software_version="s1",
    )


def test_ingest_accepts_and_deduplicates_by_idempotency() -> None:
    client = TestClient(app)
    payload = _payload()
    headers = {"X-Idempotency-Key": payload.idempotency_key}
    form_data = {"event_json": payload.model_dump_json()}

    first = client.post("/ingest", data=form_data, headers=headers)
    second = client.post("/ingest", data=form_data, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"


def test_ingest_rejects_invalid_idempotency_header() -> None:
    client = TestClient(app)
    payload = _payload()
    form_data = {"event_json": payload.model_dump_json()}

    result = client.post(
        "/ingest",
        data=form_data,
        headers={"X-Idempotency-Key": "mismatch"},
    )

    assert result.status_code == 400


def test_ingest_accepts_evidence_files() -> None:
    client = TestClient(app)
    payload = _payload()
    headers = {"X-Idempotency-Key": payload.idempotency_key}

    response = client.post(
        "/ingest",
        data={"event_json": payload.model_dump_json()},
        files={"evidence_0": ("annotated_frame.jpg", b"fakejpg", "image/jpeg")},
        headers=headers,
    )

    assert response.status_code == 200
