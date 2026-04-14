"""Data update coordinators for Mitchell Shire Council."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BINS,
    API_EVENTS,
    API_NEWS,
    CONF_BIN_SCAN_INTERVAL,
    CONF_ZONE,
    DEFAULT_BIN_SCAN_INTERVAL_HOURS,
    DOMAIN,
    EVENTS_NEWS_SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class BinData:
    """Parsed data for a single bin type."""

    def __init__(self, raw: dict) -> None:
        self.title: str = raw["title"]
        self.color: str = raw["color"]
        self.intervals: str = raw.get("intervals", "")
        self.is_recurring: bool = raw.get("isRecurring", False)
        self.description: str = raw.get("description", "")

        today = date.today()
        all_dates = [
            date.fromisoformat(d["date"])
            for d in raw.get("collectionDates", [])
        ]
        self.upcoming: list[date] = sorted(d for d in all_dates if d >= today)

    @property
    def next_collection(self) -> date | None:
        return self.upcoming[0] if self.upcoming else None

    @property
    def days_until_next(self) -> int | None:
        if self.next_collection is None:
            return None
        return (self.next_collection - date.today()).days

    @property
    def day_of_week(self) -> str | None:
        if self.next_collection is None:
            return None
        return self.next_collection.strftime("%A")

    @property
    def upcoming_iso(self) -> list[str]:
        return [d.isoformat() for d in self.upcoming[:8]]


@dataclass
class EventItem:
    """A single council event."""
    title: str
    url: str
    image: str
    event_date: datetime

    @classmethod
    def from_raw(cls, raw: dict) -> "EventItem":
        return cls(
            title=raw["title"],
            url=raw.get("url", ""),
            image=raw.get("image", ""),
            event_date=datetime.strptime(raw["postDate"], "%Y-%m-%d %H:%M:%S"),
        )

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "date": self.event_date.isoformat(),
        }


@dataclass
class NewsItem:
    """A single council news article."""
    title: str
    url: str
    image: str
    published: datetime
    featured: bool

    @classmethod
    def from_raw(cls, raw: dict) -> "NewsItem":
        return cls(
            title=raw["title"],
            url=raw.get("url", ""),
            image=raw.get("image", ""),
            published=datetime.strptime(raw["postDate"], "%Y-%m-%d %H:%M:%S"),
            featured=bool(raw.get("newsFeatureOnHomepage", False)),
        )

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "published": self.published.isoformat(),
            "featured": self.featured,
        }


@dataclass
class EventsNewsData:
    """Events and news fetched together."""
    events: list[EventItem] = field(default_factory=list)
    news: list[NewsItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _get_zone_coords(hass: HomeAssistant, zone_entity_id: str) -> tuple[float, float]:
    """Return (lat, lng) for a zone entity, or raise UpdateFailed."""
    zone_state = hass.states.get(zone_entity_id)
    if zone_state is None:
        raise UpdateFailed(
            f"Zone entity '{zone_entity_id}' not found. "
            "Check that the zone still exists in Home Assistant."
        )
    lat = zone_state.attributes.get("latitude")
    lng = zone_state.attributes.get("longitude")
    if lat is None or lng is None:
        raise UpdateFailed(
            f"Zone '{zone_entity_id}' is missing latitude/longitude attributes."
        )
    return lat, lng


# ---------------------------------------------------------------------------
# Bin coordinator — daily at BIN_REFRESH_HOUR local time
# ---------------------------------------------------------------------------

class BinCoordinator(DataUpdateCoordinator[dict[str, BinData]]):
    """Fetches bin collection data on a configurable interval (default 50 h)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        hours = entry.options.get(
            CONF_BIN_SCAN_INTERVAL,
            entry.data.get(CONF_BIN_SCAN_INTERVAL, DEFAULT_BIN_SCAN_INTERVAL_HOURS),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_bins",
            update_interval=timedelta(hours=hours),
        )
        self._entry = entry

    async def _async_update_data(self) -> dict[str, BinData]:
        zone_entity_id = self._entry.data[CONF_ZONE]
        lat, lng = _get_zone_coords(self.hass, zone_entity_id)

        session = async_get_clientsession(self.hass)
        payload = await _fetch(session, API_BINS.format(lat=lat, lng=lng))

        raw_bins = payload.get("data", [])
        if not raw_bins:
            raise UpdateFailed(
                f"No bin collection data returned for zone '{zone_entity_id}'. "
                "The coordinates may be outside the Mitchell Shire council area."
            )

        bins = {b.color: b for item in raw_bins if (b := BinData(item))}
        _LOGGER.debug("Fetched %d bin types for zone %s", len(bins), zone_entity_id)
        return bins


# ---------------------------------------------------------------------------
# Events/news coordinator — every EVENTS_NEWS_SCAN_INTERVAL_MINUTES
# ---------------------------------------------------------------------------

class EventsNewsCoordinator(DataUpdateCoordinator[EventsNewsData]):
    """Fetches council events and news every 120 minutes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_events_news",
            update_interval=timedelta(minutes=EVENTS_NEWS_SCAN_INTERVAL_MINUTES),
        )
        self._entry = entry

    async def _async_update_data(self) -> EventsNewsData:
        zone_entity_id = self._entry.data[CONF_ZONE]
        lat, lng = _get_zone_coords(self.hass, zone_entity_id)

        session = async_get_clientsession(self.hass)
        events_payload, news_payload = await asyncio.gather(
            _fetch(session, API_EVENTS.format(lat=lat, lng=lng)),
            _fetch(session, API_NEWS.format(lat=lat, lng=lng)),
        )

        events = sorted(
            (EventItem.from_raw(e) for e in events_payload.get("data", [])),
            key=lambda e: e.event_date,
        )
        news = [NewsItem.from_raw(n) for n in news_payload.get("data", [])]

        _LOGGER.debug(
            "Fetched %d events, %d news items for zone %s",
            len(events), len(news), zone_entity_id,
        )
        return EventsNewsData(events=events, news=news)


# ---------------------------------------------------------------------------
# Shared fetch helper
# ---------------------------------------------------------------------------

async def _fetch(session, url: str) -> dict:
    """Fetch a single API endpoint and return the parsed JSON."""
    try:
        async with session.get(url, timeout=30) as response:
            if response.status != 200:
                raise UpdateFailed(f"API request to {url} failed with HTTP {response.status}")
            return await response.json(content_type=None)
    except UpdateFailed:
        raise
    except Exception as err:
        raise UpdateFailed(f"Error communicating with API ({url}): {err}") from err
