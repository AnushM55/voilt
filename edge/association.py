"""Detection association utilities for bike/person grouping."""

from __future__ import annotations

from collections import defaultdict

from edge.types import Detection


def center_inside(inner: Detection, outer: Detection) -> bool:
    """Return true when inner center lies inside outer bbox."""

    cx = (inner.bbox.x1 + inner.bbox.x2) / 2.0
    cy = (inner.bbox.y1 + inner.bbox.y2) / 2.0
    return outer.bbox.x1 <= cx <= outer.bbox.x2 and outer.bbox.y1 <= cy <= outer.bbox.y2


def group_people_by_motorcycle(detections: list[Detection]) -> dict[int, list[Detection]]:
    """Associate rider/pillion/no_helmet detections with each motorcycle index."""

    motorcycles = [det for det in detections if det.label == "motorcycle"]
    people = [det for det in detections if det.label in {"rider", "pillion", "no_helmet"}]
    grouped: dict[int, list[Detection]] = defaultdict(list)
    for person in people:
        for index, motorcycle in enumerate(motorcycles):
            if center_inside(person, motorcycle):
                grouped[index].append(person)
                break
    return grouped
