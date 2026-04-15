# Home Assistant Mitchell Shire Council Integration

[![GitHub release](https://img.shields.io/github/release/jamesd/ha-mitchell-shire.svg)](https://github.com/jamesd/ha-mitchell-shire/releases)
[![License](https://img.shields.io/github/license/jamesd/ha-mitchell-shire.svg)](LICENSE)

A Home Assistant custom integration for residents of Mitchell Shire, Victoria. Provides bin collection schedules, council events, and news — all sourced from the Mitchell Shire Council public API based on your home location.

## Features

### Bin Collection
- **Next Collection Date**: Date sensor per bin type (red, green, yellow, purple)
- **Days Until Collection**: How many days until the next pickup
- **Collection Schedule**: Upcoming collection dates and day-of-week
- **Bin Calendars**: One calendar entity per bin type for schedule overview

### Council Events
- **Next Event Sensor**: Title of the next upcoming council event with date and URL
- **Council Events Calendar**: Full calendar view of upcoming council events

### Council News
- **Latest News Sensor**: Most recent news headline with publication date and URL
- **Articles List**: Full list of recent articles available as sensor attributes

## Quick Start

### Prerequisites
- Home Assistant 2023.11.0 or later
- A [zone](https://www.home-assistant.io/integrations/zone/) entity configured in Home Assistant (the default `zone.home` works)
- The zone must be within the Mitchell Shire council area

### Installation

#### HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu and select **Custom repositories**
4. Add `https://github.com/jamesd/ha-mitchell-shire` with category **Integration**
5. Find and install **Mitchell Shire Council**
6. Restart Home Assistant

#### Manual
1. Download the latest release from [GitHub](https://github.com/jamesd/ha-mitchell-shire/releases)
2. Copy the `custom_components/mitchell_shire/` folder into your HA `config/custom_components/` directory
3. Restart Home Assistant

### Add the Integration
1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Mitchell Shire**
4. Select the zone entity to use for location lookup (defaults to `zone.home`)
5. Click **Submit**

Entities are created automatically based on what the API returns for your location.

## Entities

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.{zone}_red_bin` | Next red bin (general waste) collection date |
| `sensor.{zone}_green_bin` | Next green bin (garden/organic) collection date |
| `sensor.{zone}_yellow_bin` | Next yellow bin (recycling) collection date |
| `sensor.{zone}_purple_bin` | Next purple bin (glass) collection date |
| `sensor.{zone}_next_event` | Title of the next upcoming council event |
| `sensor.{zone}_latest_news` | Latest council news headline |

Bin sensors use the `DATE` device class and include these extra attributes:

| Attribute | Description |
|-----------|-------------|
| `days_until_collection` | Days until the next pickup |
| `collection_interval` | How often this bin is collected (e.g. fortnightly) |
| `day_of_week` | Day collections fall on |
| `upcoming_collections` | List of upcoming collection dates |
| `description` | Bin type description from the council |

### Calendars

| Entity | Description |
|--------|-------------|
| `calendar.{zone}_red_bin` | Red bin collection schedule |
| `calendar.{zone}_green_bin` | Green bin collection schedule |
| `calendar.{zone}_yellow_bin` | Yellow bin collection schedule |
| `calendar.{zone}_purple_bin` | Purple bin collection schedule |
| `calendar.{zone}_council_events` | Upcoming Mitchell Shire council events |

> Not all bin types may appear — only those returned by the API for your address are created.

## Configuration

Setup requires only a zone entity. The integration uses the zone's latitude and longitude to query the Mitchell Shire Council API.

| Setting | Description | Default |
|---------|-------------|---------|
| **Zone** | A Home Assistant zone entity within the Mitchell Shire area | `zone.home` |
| **Bin refresh interval** | How often to refresh bin collection schedules (hours, 1–168) | `50` |
| **Enable council events** | Create sensors and a calendar for upcoming council events | `true` |
| **Enable council news** | Create a sensor for the latest council news | `true` |

| Data | Refresh schedule |
|------|-----------------|
| Bin collection schedules | Every **50 hours** (configurable) |
| Council events & news | Every **120 minutes** |

The bin interval can be changed after setup via the integration's **Configure** button in Settings → Devices & Services.

## Troubleshooting

### No entities created after setup
- Confirm your zone is within the Mitchell Shire council area
- Check that the zone has valid coordinates (latitude/longitude)
- Review Home Assistant logs for errors from `custom_components.mitchell_shire`

### Bin sensors missing a colour
Only bin types returned by the council API for your address are created. Not every property has all four bin types.

### Stale data
Bin data refreshes every 50 hours by default (configurable); events and news refresh every 120 minutes. To force an immediate refresh, go to **Settings** → **Devices & Services**, find the Mitchell Shire integration, and reload it.

### Debug Logging
```yaml
# Add to configuration.yaml
logger:
  default: warning
  logs:
    custom_components.mitchell_shire: debug
```

## Examples

### Dashboard Card
[`example.yaml`](example.yaml) — A vertical-stack card that shows only the bins due within the next 4 days. Each bin row collapses automatically when not due soon. Requires [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom).

### Bin Reminder Automation
[`example_automation.yaml`](example_automation.yaml) — Sends a notification at 18:00 the evening before any bin is due. Delivers a single grouped message (e.g. "Rubbish bin and FOGO bin need to go out tonight") to all devices in a configurable list.

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/jamesd/ha-mitchell-shire).

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Support

- **Bug Reports**: [GitHub Issues](https://github.com/jamesd/ha-mitchell-shire/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jamesd/ha-mitchell-shire/discussions)
- **Community**: [Home Assistant Community Forum](https://community.home-assistant.io/)

---

> Data provided by Mitchell Shire Council. This integration is not affiliated with or endorsed by Mitchell Shire Council.
