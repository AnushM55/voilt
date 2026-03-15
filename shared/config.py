"""Shared configuration primitives used by edge and server."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Common settings with environment variable loading."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="voilt")
    environment: str = Field(default="dev")
    log_level: str = Field(default="INFO")
