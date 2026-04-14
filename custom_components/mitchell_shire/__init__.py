"""Mitchell Shire Council integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENABLE_EVENTS,
    CONF_ENABLE_NEWS,
    DEFAULT_ENABLE_EVENTS,
    DEFAULT_ENABLE_NEWS,
    DOMAIN,
)
from .coordinator import BinCoordinator, EventsNewsCoordinator

PLATFORMS = ["sensor", "calendar"]


def _get_opt(entry: ConfigEntry, key: str, default) -> bool:
    return entry.options.get(key, entry.data.get(key, default))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mitchell Shire Council from a config entry."""
    bin_coordinator = BinCoordinator(hass, entry)
    await bin_coordinator.async_config_entry_first_refresh()

    enable_events = _get_opt(entry, CONF_ENABLE_EVENTS, DEFAULT_ENABLE_EVENTS)
    enable_news = _get_opt(entry, CONF_ENABLE_NEWS, DEFAULT_ENABLE_NEWS)

    events_news_coordinator: EventsNewsCoordinator | None = None
    if enable_events or enable_news:
        events_news_coordinator = EventsNewsCoordinator(hass, entry)
        await events_news_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "bin": bin_coordinator,
        "events_news": events_news_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the entry when options change so entity additions/removals take effect
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
