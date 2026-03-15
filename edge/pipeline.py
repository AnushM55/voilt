"""Edge processing pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from edge.association import group_people_by_motorcycle
from edge.config import EdgeSettings
from edge.detector import Detector
from edge.events import build_violation_event
from edge.evidence import collect_evidence
from edge.location import LocationProvider
from edge.queue import SQLiteEventQueue
from edge.rules import dedup_filter, evaluate_violations
from edge.tracker_engine import SimpleTracker
from edge.tracking import TrackState
from edge.types import Detection, FrameInput
from shared.schemas import BBox


@dataclass
class ProcessResult:
    """Single-frame processing output."""

    detections: list[Detection]
    enqueued_events: int


class EdgePipeline:
    """Coordinates detect -> associate -> rule -> emit -> queue."""

    def __init__(
        self,
        *,
        settings: EdgeSettings,
        detector: Detector,
        queue: SQLiteEventQueue,
        location_provider: LocationProvider,
    ) -> None:
        self._settings = settings
        self._detector = detector
        self._queue = queue
        self._location_provider = location_provider
        self._tracker = SimpleTracker()

    def process_frame(self, frame: FrameInput) -> int:
        """Process one frame and enqueue emitted events."""

        return self.process_frame_with_details(frame).enqueued_events

    def process_frame_with_details(self, frame: FrameInput) -> ProcessResult:
        """Process one frame and return detections plus enqueue count."""

        detections = self._detector.detect(frame)
        motorcycles = [det for det in detections if det.label == "motorcycle"]
        grouped_people = group_people_by_motorcycle(detections)
        matches = self._tracker.update(motorcycles)

        enqueued = 0
        for match in matches:
            track = self._tracker.tracks[match.track_id]
            self._update_track(
                track,
                match.motorcycle,
                grouped_people.get(match.detection_index, []),
            )
            candidates = evaluate_violations(track, self._settings)
            to_emit = dedup_filter(
                track, candidates, cooldown_seconds=self._settings.cooldown_seconds
            )
            if not to_emit:
                continue
            event = build_violation_event(
                track=track,
                violations=to_emit,
                location=self._location_provider.get_location(),
                settings=self._settings,
                evidence=(
                    collect_evidence(
                        frame=frame,
                        detections=detections,
                        violations=to_emit,
                        track=track,
                        base_dir=self._settings.evidence_dir,
                    )
                    if self._settings.capture_evidence
                    else []
                ),
            )
            self._queue.enqueue(event)
            enqueued += 1
        return ProcessResult(detections=detections, enqueued_events=enqueued)

    @staticmethod
    def _update_track(
        track: TrackState, motorcycle: Detection, associated_people: list[Detection]
    ) -> None:
        track.motorcycle_bbox = BBox(
            x1=motorcycle.bbox.x1,
            y1=motorcycle.bbox.y1,
            x2=motorcycle.bbox.x2,
            y2=motorcycle.bbox.y2,
        )
        track.stable_frames += 1
        track.max_confidence = max(track.max_confidence, motorcycle.confidence)
        track.rider_count = sum(1 for person in associated_people if person.label == "rider")
        track.pillion_count = sum(1 for person in associated_people if person.label == "pillion")
        track.no_helmet_count = sum(
            1 for person in associated_people if person.label == "no_helmet"
        )
