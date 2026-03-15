"""Simple in-memory tracker model for edge detections."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shared.schemas import BBox

if TYPE_CHECKING:
    from shared.schemas import ViolationType


@dataclass
class TrackState:
    """Lightweight track state used for rule evaluation and dedup."""

    track_id: str
    motorcycle_bbox: BBox
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    stable_frames: int = 0
    rider_count: int = 0
    pillion_count: int = 0
    no_helmet_count: int = 0
    max_confidence: float = 0.0
    emitted_violations: set[ViolationType] = field(default_factory=set)
    last_emitted_epoch: dict[str, float] = field(default_factory=dict)
