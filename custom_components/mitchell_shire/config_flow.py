"""Config flow for Mitchell Shire Council."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BIN_SCAN_INTERVAL,
    CONF_ENABLE_EVENTS,
    CONF_ENABLE_NEWS,
    CONF_ZONE,
    DEFAULT_BIN_SCAN_INTERVAL_HOURS,
    DEFAULT_ENABLE_EVENTS,
    DEFAULT_ENABLE_NEWS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _get_opt(entry: ConfigEntry, key: str, default: Any) -> Any:
    """Read from options, falling back to data, then the provided default."""
    return entry.options.get(key, entry.data.get(key, default))


class MitchellShireConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mitchell Shire Council."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            zone_entity_id = user_input[CONF_ZONE]

            await self.async_set_unique_id(zone_entity_id)
            self._abort_if_unique_id_configured()

            zone_state = self.hass.states.get(zone_entity_id)
            if zone_state is None:
                errors[CONF_ZONE] = "zone_not_found"
            elif zone_state.attributes.get("latitude") is None:
                errors[CONF_ZONE] = "zone_no_coordinates"
            else:
                zone_name = zone_state.attributes.get("friendly_name", zone_entity_id)
                return self.async_create_entry(
                    title=f"Mitchell Shire ({zone_name})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ZONE, default="zone.home"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="zone")
                    ),
                    vol.Optional(
                        CONF_BIN_SCAN_INTERVAL,
                        default=DEFAULT_BIN_SCAN_INTERVAL_HOURS,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=168,
                            step=1,
                            unit_of_measurement="hours",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_ENABLE_EVENTS,
                        default=DEFAULT_ENABLE_EVENTS,
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_ENABLE_NEWS,
                        default=DEFAULT_ENABLE_NEWS,
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MitchellShireOptionsFlow()


class MitchellShireOptionsFlow(OptionsFlow):
    """Allow bin interval and events/news toggles to be changed after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_BIN_SCAN_INTERVAL,
                        default=_get_opt(self.config_entry, CONF_BIN_SCAN_INTERVAL, DEFAULT_BIN_SCAN_INTERVAL_HOURS),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=168,
                            step=1,
                            unit_of_measurement="hours",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_ENABLE_EVENTS,
                        default=_get_opt(self.config_entry, CONF_ENABLE_EVENTS, DEFAULT_ENABLE_EVENTS),
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_ENABLE_NEWS,
                        default=_get_opt(self.config_entry, CONF_ENABLE_NEWS, DEFAULT_ENABLE_NEWS),
                    ): selector.BooleanSelector(),
                }
            ),
        )
