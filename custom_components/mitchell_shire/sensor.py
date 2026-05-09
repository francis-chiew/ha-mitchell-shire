"""Sensor platform for Mitchell Shire Council."""
from __future__ import annotations

import logging
from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    BIN_ICONS,
    BIN_MDI_ICONS,
    CONF_ENABLE_EVENTS,
    CONF_ENABLE_NEWS,
    DEFAULT_ENABLE_EVENTS,
    DEFAULT_ENABLE_NEWS,
    DOMAIN,
)
from .coordinator import BinCoordinator, BinData, EventsNewsCoordinator, EventsNewsData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mitchell Shire sensors from a config entry."""
    coordinators = hass.data[DOMAIN][entry.entry_id]
    bin_coordinator: BinCoordinator = coordinators["bin"]
    events_news_coordinator: EventsNewsCoordinator | None = coordinators["events_news"]

    entities: list[SensorEntity] = []
    for color in bin_coordinator.data:
        entities.append(BinSensor(bin_coordinator, entry.entry_id, color))
        entities.append(BinCountdownSensor(bin_coordinator, entry.entry_id, color))

    if events_news_coordinator is not None:
        enable_events = entry.options.get(CONF_ENABLE_EVENTS, entry.data.get(CONF_ENABLE_EVENTS, DEFAULT_ENABLE_EVENTS))
        enable_news = entry.options.get(CONF_ENABLE_NEWS, entry.data.get(CONF_ENABLE_NEWS, DEFAULT_ENABLE_NEWS))

        if enable_events:
            entities.append(EventsSensor(events_news_coordinator, entry.entry_id))
        if enable_news:
            entities.append(NewsSensor(events_news_coordinator, entry.entry_id))

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Bin sensors
# ---------------------------------------------------------------------------

class BinSensor(CoordinatorEntity[BinCoordinator], SensorEntity):
    """Next collection date for one bin type."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(
        self,
        coordinator: BinCoordinator,
        entry_id: str,
        color: str,
    ) -> None:
        super().__init__(coordinator)
        self._color = color
        self._attr_unique_id = f"{entry_id}_{color}_bin"
        self._attr_entity_picture = BIN_ICONS.get(color)
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
    def native_value(self) -> date | None:
        bin_data = self._bin
        return bin_data.next_collection if bin_data else None

    @property
    def extra_state_attributes(self) -> dict:
        bin_data = self._bin
        if bin_data is None:
            return {}
        return {
            "days_until_collection": bin_data.days_until_next,
            "collection_interval": bin_data.intervals,
            "day_of_week": bin_data.day_of_week,
            "upcoming_collections": bin_data.upcoming_iso,
            "description": bin_data.description,
        }


class BinCountdownSensor(CoordinatorEntity[BinCoordinator], SensorEntity):
    """Days until next collection for one bin type — numeric state for conditional cards."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "d"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:counter"

    def __init__(
        self,
        coordinator: BinCoordinator,
        entry_id: str,
        color: str,
    ) -> None:
        super().__init__(coordinator)
        self._color = color
        self._attr_unique_id = f"{entry_id}_{color}_days_until"

    @property
    def _bin(self) -> BinData | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._color)

    @property
    def name(self) -> str:
        bin_data = self._bin
        title = bin_data.title if bin_data else self._color.capitalize()
        return f"{title} Days"

    @property
    def native_value(self) -> int | None:
        bin_data = self._bin
        return bin_data.days_until_next if bin_data else None


# ---------------------------------------------------------------------------
# Events sensor
# ---------------------------------------------------------------------------

class EventsSensor(CoordinatorEntity[EventsNewsCoordinator], SensorEntity):
    """Next upcoming council event."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar"

    def __init__(self, coordinator: EventsNewsCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_events"
        self._attr_name = "Next Event"

    @property
    def _data(self) -> EventsNewsData | None:
        return self.coordinator.data

    @property
    def native_value(self) -> str | None:
        if self._data is None or not self._data.events:
            return None
        return self._data.events[0].title

    @property
    def extra_state_attributes(self) -> dict:
        if self._data is None:
            return {}
        events = self._data.events
        if not events:
            return {"events": []}
        next_event = events[0]
        return {
            "next_event_date": next_event.event_date.isoformat(),
            "next_event_url": next_event.url,
            "events": [e.as_dict() for e in events],
        }


# ---------------------------------------------------------------------------
# News sensor
# ---------------------------------------------------------------------------

class NewsSensor(CoordinatorEntity[EventsNewsCoordinator], SensorEntity):
    """Latest Mitchell Shire council news headline."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_icon = "mdi:newspaper"

    def __init__(self, coordinator: EventsNewsCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_news"
        self._attr_name = "Latest News"

    @property
    def _data(self) -> EventsNewsData | None:
        return self.coordinator.data

    @property
    def native_value(self) -> str | None:
        if self._data is None or not self._data.news:
            return None
        return self._data.news[0].title

    @property
    def extra_state_attributes(self) -> dict:
        if self._data is None:
            return {}
        news = self._data.news
        if not news:
            return {"articles": []}
        latest = news[0]
        return {
            "latest_published": latest.published.isoformat(),
            "latest_url": latest.url,
            "featured": latest.featured,
            "articles": [n.as_dict() for n in news],
        }
