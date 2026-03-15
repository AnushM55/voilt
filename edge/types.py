"""Edge-internal detection and frame models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shared.schemas import BBox


@dataclass(frozen=True)
class Detection:
    """Single model detection in current frame."""

    label: str
    confidence: float
    bbox: BBox


@dataclass(frozen=True)
class FrameInput:
    """Frame wrapper consumed by detector and pipeline."""

    frame_id: int
    width: int
    height: int
    image: Any | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
