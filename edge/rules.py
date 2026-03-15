"""Violation rule engine with temporal stability and dedup support."""

from __future__ import annotations

import time

from edge.config import EdgeSettings
from edge.tracking import TrackState
from shared.schemas import ViolationType


def evaluate_violations(track: TrackState, settings: EdgeSettings) -> list[ViolationType]:
    """Evaluate violations once track has enough stable frames."""

    if track.stable_frames < settings.min_stable_frames:
        return []

    found: list[ViolationType] = []
    if track.no_helmet_count > 0:
        found.append(ViolationType.NO_HELMET)
    if (track.rider_count + track.pillion_count) >= 3:
        found.append(ViolationType.TRIPLE_RIDING)
    return found


def dedup_filter(
    track: TrackState,
    candidates: list[ViolationType],
    cooldown_seconds: int,
) -> list[ViolationType]:
    """Suppress duplicate emissions for already emitted violations."""

    now = time.time()
    emit: list[ViolationType] = []
    for violation in candidates:
        key = violation.value
        last_emitted = track.last_emitted_epoch.get(key)
        if last_emitted is not None and (now - last_emitted) < cooldown_seconds:
            continue
        track.last_emitted_epoch[key] = now
        track.emitted_violations.add(violation)
        emit.append(violation)
    return emit
