from pathlib import Path

import numpy as np

from edge.config import EdgeSettings
from edge.detector import StubDetector
from edge.location import LocationProvider
from edge.pipeline import EdgePipeline
from edge.queue import SQLiteEventQueue
from edge.types import Detection, FrameInput
from shared.schemas import BBox


def test_pipeline_emits_single_event_for_stable_track(tmp_path: Path) -> None:
    detections = [
        Detection("motorcycle", 0.9, BBox(x1=10, y1=10, x2=110, y2=110)),
        Detection("rider", 0.8, BBox(x1=30, y1=20, x2=70, y2=90)),
        Detection("pillion", 0.8, BBox(x1=60, y1=20, x2=90, y2=95)),
        Detection("pillion", 0.8, BBox(x1=20, y1=30, x2=50, y2=100)),
        Detection("no_helmet", 0.85, BBox(x1=32, y1=20, x2=68, y2=55)),
    ]
    settings = EdgeSettings(
        min_stable_frames=1,
        cooldown_seconds=999,
        queue_db_path=str(tmp_path / "q.db"),
        evidence_dir=str(tmp_path / "evidence"),
    )
    queue = SQLiteEventQueue(settings.queue_db_path)
    provider = LocationProvider()
    provider.update_from_network(12.0, 77.0, 120.0, "ip")
    pipeline = EdgePipeline(
        settings=settings,
        detector=StubDetector(detections=detections),
        queue=queue,
        location_provider=provider,
    )

    enqueued_first = pipeline.process_frame(FrameInput(frame_id=1, width=1280, height=720))
    enqueued_second = pipeline.process_frame(FrameInput(frame_id=2, width=1280, height=720))

    assert enqueued_first == 1
    assert enqueued_second == 0
    leased = queue.lease(limit=1)
    assert leased[0].event.violations
    assert len(leased[0].event.violations) == 2


def test_pipeline_attaches_annotated_evidence_when_image_present(tmp_path: Path) -> None:
    detections = [
        Detection("motorcycle", 0.9, BBox(x1=10, y1=10, x2=110, y2=110)),
        Detection("rider", 0.8, BBox(x1=30, y1=20, x2=70, y2=90)),
        Detection("pillion", 0.8, BBox(x1=60, y1=20, x2=90, y2=95)),
        Detection("pillion", 0.8, BBox(x1=20, y1=30, x2=50, y2=100)),
        Detection("no_helmet", 0.85, BBox(x1=32, y1=20, x2=68, y2=55)),
    ]
    settings = EdgeSettings(
        min_stable_frames=1,
        cooldown_seconds=999,
        queue_db_path=str(tmp_path / "q.db"),
        evidence_dir=str(tmp_path / "evidence"),
    )
    queue = SQLiteEventQueue(settings.queue_db_path)
    provider = LocationProvider()
    provider.update_from_network(12.0, 77.0, 120.0, "ip")
    pipeline = EdgePipeline(
        settings=settings,
        detector=StubDetector(detections=detections),
        queue=queue,
        location_provider=provider,
    )

    frame = FrameInput(
        frame_id=1, width=1280, height=720, image=np.zeros((720, 1280, 3), dtype=np.uint8)
    )
    enqueued = pipeline.process_frame(frame)
    assert enqueued == 1
    leased = queue.lease(limit=1)
    assert leased[0].event.evidence
    kinds = {item.kind for item in leased[0].event.evidence}
    assert "annotated_frame" in kinds
