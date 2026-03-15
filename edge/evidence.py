"""Evidence extraction and persistence helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import cv2

from edge.tracking import TrackState
from edge.types import Detection, FrameInput
from shared.schemas import EvidenceRef, ViolationType


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def collect_evidence(
    *,
    frame: FrameInput,
    detections: list[Detection],
    violations: list[ViolationType],
    track: TrackState,
    base_dir: str,
) -> list[EvidenceRef]:
    """Persist annotated frame and motorcycle crop, return evidence references."""

    if frame.image is None:
        return []

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    event_dir = Path(base_dir) / track.track_id / stamp
    event_dir.mkdir(parents=True, exist_ok=True)

    annotated = frame.image.copy()
    for detection in detections:
        x1 = int(detection.bbox.x1)
        y1 = int(detection.bbox.y1)
        x2 = int(detection.bbox.x2)
        y2 = int(detection.bbox.y2)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(
            annotated,
            f"{detection.label}:{detection.confidence:.2f}",
            (x1, max(12, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

    tx1 = _clamp(int(track.motorcycle_bbox.x1), 0, frame.width - 1)
    ty1 = _clamp(int(track.motorcycle_bbox.y1), 0, frame.height - 1)
    tx2 = _clamp(int(track.motorcycle_bbox.x2), tx1 + 1, frame.width)
    ty2 = _clamp(int(track.motorcycle_bbox.y2), ty1 + 1, frame.height)
    cv2.rectangle(annotated, (tx1, ty1), (tx2, ty2), (0, 0, 255), 2)
    cv2.putText(
        annotated,
        f"track={track.track_id} violations={','.join(v.value for v in violations)}",
        (tx1, min(frame.height - 8, ty2 + 16)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        1,
        cv2.LINE_AA,
    )

    refs: list[EvidenceRef] = []
    annotated_path = event_dir / "annotated_frame.jpg"
    cv2.imwrite(str(annotated_path), annotated)
    refs.append(
        EvidenceRef(kind="annotated_frame", uri=str(annotated_path), score=track.max_confidence)
    )

    motorcycle_crop = annotated[ty1:ty2, tx1:tx2]
    motorcycle_path = event_dir / "motorcycle_crop.jpg"
    cv2.imwrite(str(motorcycle_path), motorcycle_crop)
    refs.append(
        EvidenceRef(kind="motorcycle_crop", uri=str(motorcycle_path), score=track.max_confidence)
    )
    return refs
