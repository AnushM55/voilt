"""CLI entrypoint for edge worker."""

from __future__ import annotations

import argparse

from edge.config import EdgeSettings
from edge.detector import StubDetector, YoloDetector
from edge.location import LocationProvider
from edge.pipeline import EdgePipeline
from edge.queue import SQLiteEventQueue
from edge.runner import run_realtime
from edge.types import Detection, FrameInput
from shared.logging import configure_logging
from shared.schemas import BBox


def run_once(demo_event: bool = False, queue_db_path: str | None = None) -> int:
    """Run single-frame edge cycle for smoke testing."""

    settings = EdgeSettings(
        queue_db_path=queue_db_path or "edge/edge_queue.db",
        min_stable_frames=1 if demo_event else 3,
    )
    configure_logging(settings.log_level)
    queue = SQLiteEventQueue(settings.queue_db_path)
    location_provider = LocationProvider()
    location_provider.update_from_network(lat=12.97, lon=77.59, accuracy_m=120.0, source="ip")

    detections: list[Detection] = []
    if demo_event:
        detections = [
            Detection("motorcycle", 0.9, BBox(x1=10, y1=10, x2=110, y2=110)),
            Detection("rider", 0.8, BBox(x1=30, y1=20, x2=70, y2=90)),
            Detection("pillion", 0.8, BBox(x1=60, y1=20, x2=90, y2=95)),
            Detection("pillion", 0.8, BBox(x1=20, y1=30, x2=50, y2=100)),
            Detection("no_helmet", 0.85, BBox(x1=32, y1=20, x2=68, y2=55)),
        ]

    pipeline = EdgePipeline(
        settings=settings,
        detector=StubDetector(detections=detections),
        queue=queue,
        location_provider=location_provider,
    )
    frame = FrameInput(frame_id=1, width=1280, height=720)
    enqueued = pipeline.process_frame(frame)
    print(f"enqueued={enqueued} queue_size={queue.size()}")
    return enqueued


def main() -> None:
    """Edge program entrypoint."""

    parser = argparse.ArgumentParser(description="voilt edge worker")
    parser.add_argument("--once", action="store_true", help="run one frame and exit")
    parser.add_argument("--realtime", action="store_true", help="run continuous realtime loop")
    parser.add_argument("--source", default="0", help="camera index or video file path")
    parser.add_argument("--model", default="", help="YOLO model path (.pt or _ncnn_model dir)")
    parser.add_argument("--conf", type=float, default=0.25, help="detection confidence threshold")
    parser.add_argument("--headless", action="store_true", help="disable display window")
    parser.add_argument("--no-upload", action="store_true", help="disable ingest uploads")
    parser.add_argument(
        "--demo-event",
        action="store_true",
        help="inject one synthetic violating frame to test queue/event path",
    )
    args = parser.parse_args()
    if args.once:
        run_once(demo_event=args.demo_event)
        return
    if args.realtime:
        settings = EdgeSettings(show_window=not args.headless)
        configure_logging(settings.log_level)
        if args.model:
            detector = YoloDetector(model_path=args.model, conf=args.conf)
        elif args.demo_event:
            detector = StubDetector(
                detections=[
                    Detection("motorcycle", 0.9, BBox(x1=10, y1=10, x2=110, y2=110)),
                    Detection("rider", 0.8, BBox(x1=30, y1=20, x2=70, y2=90)),
                    Detection("pillion", 0.8, BBox(x1=60, y1=20, x2=90, y2=95)),
                    Detection("pillion", 0.8, BBox(x1=20, y1=30, x2=50, y2=100)),
                    Detection("no_helmet", 0.85, BBox(x1=32, y1=20, x2=68, y2=55)),
                ]
            )
        else:
            detector = StubDetector()
        run_realtime(
            settings=settings,
            detector=detector,
            source=args.source,
            headless=args.headless,
            upload=not args.no_upload,
        )


if __name__ == "__main__":
    main()
