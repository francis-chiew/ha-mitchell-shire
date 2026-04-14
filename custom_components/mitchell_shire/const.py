"""Constants for the Mitchell Shire Council integration."""

DOMAIN = "mitchell_shire"

CONF_ZONE = "zone"
CONF_BIN_SCAN_INTERVAL = "bin_scan_interval"
CONF_ENABLE_EVENTS = "enable_events"
CONF_ENABLE_NEWS = "enable_news"

DEFAULT_BIN_SCAN_INTERVAL_HOURS = 50
DEFAULT_ENABLE_EVENTS = True
DEFAULT_ENABLE_NEWS = True
EVENTS_NEWS_SCAN_INTERVAL_MINUTES = 120

API_BASE = "https://www.mitchellshire.vic.gov.au/simple-gov-app/api/resources"
API_BINS = API_BASE + "/bin-collections/search?lat={lat}&lng={lng}"
API_EVENTS = API_BASE + "/events/search?lat={lat}&lng={lng}"
API_NEWS = API_BASE + "/news/search?lat={lat}&lng={lng}"

ATTRIBUTION = (
    "Data provided by Mitchell Shire Council. "
    "This integration is not affiliated with or endorsed by Mitchell Shire Council."
)

BIN_ICON_BASE = (
    "https://www.mitchellshire.vic.gov.au/dist/build/static/icons/Bins/{color}.svg"
)

BIN_ICONS: dict[str, str] = {
    "red": BIN_ICON_BASE.format(color="red"),
    "green": BIN_ICON_BASE.format(color="green"),
    "yellow": BIN_ICON_BASE.format(color="yellow"),
    "purple": BIN_ICON_BASE.format(color="purple"),
}

BIN_MDI_ICONS: dict[str, str] = {
    "red": "mdi:trash-can",
    "green": "mdi:leaf",
    "yellow": "mdi:recycle",
    "purple": "mdi:bottle-wine",
}
