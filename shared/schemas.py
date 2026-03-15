"""Shared event schemas used by edge and server."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class ViolationType(StrEnum):
    """Supported violation types emitted by edge."""

    NO_HELMET = "no_helmet"
    TRIPLE_RIDING = "triple_riding"


class LocationSource(StrEnum):
    """Location provenance used for coarse positioning."""

    WIFI = "wifi"
    IP = "ip"
    CACHED = "cached"
    UNKNOWN = "unknown"


class BBox(BaseModel):
    """Normalized box coordinates in frame space."""

    x1: float = Field(ge=0.0)
    y1: float = Field(ge=0.0)
    x2: float = Field(gt=0.0)
    y2: float = Field(gt=0.0)

    @field_validator("x2")
    @classmethod
    def x2_gt_x1(cls, value: float, info: ValidationInfo) -> float:
        values = info.data
        x1 = values.get("x1")
        if x1 is not None and value <= x1:
            raise ValueError("x2 must be greater than x1")
        return value

    @field_validator("y2")
    @classmethod
    def y2_gt_y1(cls, value: float, info: ValidationInfo) -> float:
        values = info.data
        y1 = values.get("y1")
        if y1 is not None and value <= y1:
            raise ValueError("y2 must be greater than y1")
        return value


class EvidenceRef(BaseModel):
    """Metadata describing evidence object references."""

    kind: str = Field(min_length=1, max_length=64)
    uri: str = Field(min_length=1, max_length=1024)
    score: float = Field(ge=0.0, le=1.0, default=0.0)


class EventLocation(BaseModel):
    """Coarse geolocation captured by edge device."""

    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    accuracy_m: float = Field(ge=0.0)
    source: LocationSource
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ViolationCounts(BaseModel):
    """Derived count metadata used by server verification."""

    rider: int = Field(ge=0, default=0)
    pillion: int = Field(ge=0, default=0)
    no_helmet: int = Field(ge=0, default=0)


class ViolationEvent(BaseModel):
    """Primary edge-to-server payload contract."""

    event_id: UUID = Field(default_factory=uuid4)
    idempotency_key: str = Field(min_length=12, max_length=128)
    device_id: str = Field(min_length=1, max_length=64)
    track_id: str = Field(min_length=1, max_length=64)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    violations: list[ViolationType] = Field(min_length=1)
    max_confidence: float = Field(ge=0.0, le=1.0)
    motorcycle_bbox: BBox
    counts: ViolationCounts = Field(default_factory=ViolationCounts)
    location: EventLocation
    model_version: str = Field(min_length=1, max_length=64)
    software_version: str = Field(min_length=1, max_length=64)
    evidence: list[EvidenceRef] = Field(default_factory=list)


class VerificationStatus(StrEnum):
    """Backend verification outcome."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class VerifiedEvent(BaseModel):
    """Post-verification server model used by API/UI."""

    event: ViolationEvent
    status: VerificationStatus
    verification_score: float = Field(ge=0.0, le=1.0)
    plate_text: str | None = Field(default=None, max_length=32)
    plate_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reason: str | None = Field(default=None, max_length=256)
    verified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
