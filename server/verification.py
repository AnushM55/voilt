"""Verification and OCR stubs for backend processing."""

from __future__ import annotations

from shared.schemas import VerificationStatus, VerifiedEvent, ViolationEvent


def verify_event(event: ViolationEvent) -> VerifiedEvent:
    """Placeholder verifier with deterministic behavior for phase scaffolding."""

    if event.max_confidence >= 0.5:
        status = VerificationStatus.ACCEPTED
        reason = None
    else:
        status = VerificationStatus.NEEDS_REVIEW
        reason = "low confidence"
    plate_text, plate_confidence = extract_plate_text(event)
    return VerifiedEvent(
        event=event,
        status=status,
        verification_score=event.max_confidence,
        plate_text=plate_text,
        plate_confidence=plate_confidence,
        reason=reason,
    )


def extract_plate_text(event: ViolationEvent) -> tuple[str | None, float | None]:
    """Phase-2 placeholder OCR extractor interface."""

    for evidence in event.evidence:
        if evidence.kind == "plate_crop":
            return "UNKNOWN", evidence.score
    return None, None
