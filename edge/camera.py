"""Camera and video source utilities for edge runtime."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import cv2

from edge.types import FrameInput


@dataclass
class VideoSourceConfig:
    """Capture source runtime settings."""

    source: str
    frame_width: int
    frame_height: int


def _resolve_source(source: str) -> int | str:
    try:
        return int(source)
    except ValueError:
        return source


class VideoSource:
    """OpenCV-based capture source for camera or file input."""

    def __init__(self, config: VideoSourceConfig) -> None:
        self._capture = cv2.VideoCapture(_resolve_source(config.source))
        if not self._capture.isOpened():
            raise RuntimeError(f"failed to open source: {config.source}")
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(config.frame_width))
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(config.frame_height))

    def frames(self) -> Iterator[FrameInput]:
        frame_id = 0
        while True:
            ok, image = self._capture.read()
            if not ok:
                break
            frame_id += 1
            height, width = image.shape[:2]
            yield FrameInput(
                frame_id=frame_id,
                width=width,
                height=height,
                image=image,
                captured_at=datetime.now(UTC),
            )

    def close(self) -> None:
        self._capture.release()
