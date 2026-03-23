"""Server runtime configuration."""

from __future__ import annotations

from pydantic import Field

from shared.config import BaseAppSettings


class ServerSettings(BaseAppSettings):
    """Settings for ingest API and persistence."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    database_url: str = Field(default="sqlite:///server/voilt.db")
