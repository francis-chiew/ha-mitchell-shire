"""Calendar platform for Mitchell Shire Council."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    BIN_MDI_ICONS,
    CONF_ENABLE_EVENTS,
    DEFAULT_ENABLE_EVENTS,
    DOMAIN,
)
from .coordinator import BinCoordinator, BinData, EventItem, EventsNewsCoordinator, EventsNewsData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitchell Shire calendar entities from a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]
    bin_coordinator: BinCoordinator = coordinators["bin"]
    events_news_coordinator: EventsNewsCoordinator | None = coordinators["events_news"]

    entities: list[CalendarEntity] = [
        BinCalendar(bin_coordinator, entry.entry_id, color)
        for color in bin_coordinator.data
    ]

    if events_news_coordinator is not None:
        enable_events = entry.options.get(CONF_ENABLE_EVENTS, entry.data.get(CONF_ENABLE_EVENTS, DEFAULT_ENABLE_EVENTS))
        if enable_events:
            entities.append(CouncilEventsCalendar(events_news_coordinator, entry.entry_id))

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Bin calendars — one per bin type, all-day events
# ---------------------------------------------------------------------------

class BinCalendar(CoordinatorEntity[BinCoordinator], CalendarEntity):
    """All-day calendar events for a single bin type's collection schedule."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BinCoordinator,
        entry_id: str,
        color: str,
    ) -> None:
        super().__init__(coordinator)
        self._color = color
        self._attr_unique_id = f"{entry_id}_{color}_bin_calendar"
        self._attr_icon = BIN_MDI_ICONS.get(color, "mdi:trash-can")

    @property
    def _bin(self) -> BinData | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._color)

    @property
    def name(self) -> str:
        bin_data = self._bin
        return bin_data.title if bin_data else self._color.capitalize()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming collection as the current calendar event."""
        bin_data = self._bin
        if bin_data is None or bin_data.next_collection is None:
            return None
        return self._make_event(bin_data, bin_data.next_collection)

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all collection events within the requested date range."""
        bin_data = self._bin
        if bin_data is None:
            return []

        range_start = start_date.date()
        range_end = end_date.date()

        return [
            self._make_event(bin_data, d)
            for d in bin_data.upcoming
            if range_start <= d < range_end
        ]

    @staticmethod
    def _make_event(bin_data: BinData, d: date) -> CalendarEvent:
        return CalendarEvent(
            start=d,
            end=d + timedelta(days=1),
            summary=bin_data.title,
            description=f"{bin_data.intervals} collection",
        )


# ---------------------------------------------------------------------------
# Council events calendar — timed events
# ---------------------------------------------------------------------------

class CouncilEventsCalendar(CoordinatorEntity[EventsNewsCoordinator], CalendarEntity):
    """Calendar events sourced from the Mitchell Shire council events feed."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-star"

    def __init__(self, coordinator: EventsNewsCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_council_events_calendar"
        self._attr_name = "Council Events"

    @property
    def _data(self) -> EventsNewsData | None:
        return self.coordinator.data

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming council event."""
        if self._data is None or not self._data.events:
            return None
        return self._make_event(self._data.events[0])

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all council events within the requested date range."""
        if self._data is None:
            return []

        return [
            self._make_event(e)
            for e in self._data.events
            if start_date <= dt_util.as_local(e.event_date) < end_date
        ]

    @staticmethod
    def _make_event(e: EventItem) -> CalendarEvent:
        start = dt_util.as_local(e.event_date)
        return CalendarEvent(
            start=start,
            end=start + timedelta(hours=1),
            summary=e.title,
            description=e.url,
        )
