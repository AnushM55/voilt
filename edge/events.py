"""Edge event builder utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from edge.config import EdgeSettings
from edge.tracking import TrackState
from shared.schemas import (
    EventLocation,
    EvidenceRef,
    ViolationCounts,
    ViolationEvent,
    ViolationType,
)


def make_idempotency_key(
    *,
    device_id: str,
    track_id: str,
    violations: list[ViolationType],
    captured_at: datetime,
) -> str:
    """Create deterministic key to deduplicate repeated uploads."""

    parts = [
        device_id,
        track_id,
        ",".join(sorted(v.value for v in violations)),
        captured_at.isoformat(),
    ]
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:32]


def build_violation_event(
    *,
    track: TrackState,
    violations: list[ViolationType],
    location: EventLocation,
    settings: EdgeSettings,
    evidence: list[EvidenceRef] | None = None,
) -> ViolationEvent:
    """Build shared payload for edge->server upload."""

    captured_at = datetime.now(UTC)
    idempotency_key = make_idempotency_key(
        device_id=settings.device_id,
        track_id=track.track_id,
        violations=violations,
        captured_at=captured_at,
    )
    return ViolationEvent(
        idempotency_key=idempotency_key,
        device_id=settings.device_id,
        track_id=track.track_id,
        captured_at=captured_at,
        violations=violations,
        max_confidence=track.max_confidence,
        motorcycle_bbox=track.motorcycle_bbox,
        counts=ViolationCounts(
            rider=track.rider_count,
            pillion=track.pillion_count,
            no_helmet=track.no_helmet_count,
        ),
        location=location,
        model_version=settings.model_version,
        software_version=settings.software_version,
        evidence=evidence or [],
    )
