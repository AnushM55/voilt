"""Coarse location provider for edge events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shared.schemas import EventLocation, LocationSource


@dataclass
class CachedLocation:
    """Cached location snapshot used when fresh lookup is unavailable."""

    lat: float
    lon: float
    accuracy_m: float
    timestamp: datetime


class LocationProvider:
    """Best-effort coarse location provider with cache fallback."""

    def __init__(self) -> None:
        self._cache: CachedLocation | None = None

    def update_from_network(
        self, lat: float, lon: float, accuracy_m: float, source: str
    ) -> EventLocation:
        resolved_source = (
            LocationSource(source)
            if source in LocationSource._value2member_map_
            else LocationSource.UNKNOWN
        )
        stamp = datetime.now(UTC)
        self._cache = CachedLocation(lat=lat, lon=lon, accuracy_m=accuracy_m, timestamp=stamp)
        return EventLocation(
            lat=lat,
            lon=lon,
            accuracy_m=accuracy_m,
            source=resolved_source,
            timestamp=stamp,
        )

    def get_location(self) -> EventLocation:
        if self._cache is None:
            return EventLocation(
                lat=0.0,
                lon=0.0,
                accuracy_m=10_000.0,
                source=LocationSource.UNKNOWN,
                timestamp=datetime.now(UTC),
            )
        return EventLocation(
            lat=self._cache.lat,
            lon=self._cache.lon,
            accuracy_m=self._cache.accuracy_m,
            source=LocationSource.CACHED,
            timestamp=datetime.now(UTC),
        )
