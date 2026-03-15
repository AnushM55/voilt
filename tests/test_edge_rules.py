from edge.config import EdgeSettings
from edge.rules import dedup_filter, evaluate_violations
from edge.tracking import TrackState
from shared.schemas import BBox, ViolationType


def test_triple_riding_and_no_helmet_rules() -> None:
    settings = EdgeSettings(min_stable_frames=3)
    track = TrackState(track_id="1", motorcycle_bbox=BBox(x1=1, y1=1, x2=2, y2=2))
    track.stable_frames = 3
    track.rider_count = 1
    track.pillion_count = 2
    track.no_helmet_count = 1

    found = evaluate_violations(track, settings)

    assert ViolationType.NO_HELMET in found
    assert ViolationType.TRIPLE_RIDING in found


def test_dedup_filter_blocks_cooldown_duplicates() -> None:
    track = TrackState(track_id="1", motorcycle_bbox=BBox(x1=1, y1=1, x2=2, y2=2))
    first = dedup_filter(track, [ViolationType.NO_HELMET], cooldown_seconds=100)
    second = dedup_filter(track, [ViolationType.NO_HELMET], cooldown_seconds=100)
    assert len(first) == 1
    assert second == []
