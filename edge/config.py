"""Edge runtime configuration."""

from __future__ import annotations

from pydantic import Field

from shared.config import BaseAppSettings


class EdgeSettings(BaseAppSettings):
    """Settings for edge processing and uplink behavior."""

    device_id: str = Field(default="pi-unknown")
    model_version: str = Field(default="yolo-ncnn-v1")
    software_version: str = Field(default="0.1.0")
    min_stable_frames: int = Field(default=3, ge=1)
    cooldown_seconds: int = Field(default=15, ge=0)
    queue_db_path: str = Field(default="edge/edge_queue.db")
    ingest_url: str = Field(default="http://localhost:8000/ingest")
    frame_width: int = Field(default=1280, ge=160)
    frame_height: int = Field(default=720, ge=120)
    max_fps: float = Field(default=15.0, gt=0.0)
    camera_index: int = Field(default=0, ge=0)
    show_window: bool = Field(default=True)
    evidence_dir: str = Field(default="edge/evidence")
    capture_evidence: bool = Field(default=True)
