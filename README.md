# Energy-Charts Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A custom Home Assistant integration for monitoring real-time energy production data from the [Energy-Charts](https://energy-charts.info) API by Fraunhofer ISE.

> **⚠️ Important:** This is an unofficial, community-developed integration. It is **not affiliated with or endorsed by** Fraunhofer ISE or Energy-Charts. The code was developed with AI assistance (Claude). See [Disclaimer](#disclaimer) for full details.

## Features

- ✅ **No API Key Required** - Public API access
- ✅ **Real-time Data** - 15-minute update intervals
- ✅ **Multiple Countries** - Support for DE, AT, CH, FR, NL, BE, PL, CZ
- ✅ **Detailed Energy Sources** - Individual sensors for each energy source (solar, wind, hydro, etc.)
- ✅ **Aggregated Sensors** - Total production, renewables, fossil fuels, nuclear
- ✅ **Category Sensors** - Solar total, wind total, hydro total, fossil total
- ✅ **Historical Data** - Optional historical data as sensor attributes
- ✅ **Configurable** - UI-based configuration with multiple options

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/philipprau/homeassistant-energy-charts`
6. Select category "Integration"
7. Click "Add"
8. Search for "Energy-Charts" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/energy_charts` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### UI Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Energy-Charts"
4. Follow the configuration steps:

#### Step 1: Basic Configuration
- **Country**: Select the country (Germany, Austria, Switzerland, etc.)
- **Update Interval**: Set update frequency in minutes (5-60, default: 15)

#### Step 2: Sensor Selection
- **Individual Energy Sources**: Enable sensors for each energy source
- **Aggregated Sensors**: Enable total production, renewable share, etc.
- **Category Sensors**: Enable solar total, wind total, hydro total, etc.
- **Forecast Sensors**: Enable forecast data (if available)

#### Step 3: Advanced Options
- **Historical Data**: Choose to include historical data (None, Day, Week, Month)
- **Language**: Select language for sensor names (en, de, fr, it, es)

## Available Sensors

### Individual Source Sensors

Individual sensors are created for each available energy source:

- `sensor.energy_charts_{country}_solar` - Solar energy production
- `sensor.energy_charts_{country}_wind_onshore` - Onshore wind production
- `sensor.energy_charts_{country}_wind_offshore` - Offshore wind production
- `sensor.energy_charts_{country}_hydro_run_of_river` - Run-of-river hydro
- `sensor.energy_charts_{country}_hydro_water_reservoir` - Reservoir hydro
- `sensor.energy_charts_{country}_hydro_pumped_storage` - Pumped storage
- `sensor.energy_charts_{country}_biomass` - Biomass production
- `sensor.energy_charts_{country}_nuclear` - Nuclear production
- `sensor.energy_charts_{country}_fossil_gas` - Natural gas production
- `sensor.energy_charts_{country}_fossil_hard_coal` - Hard coal production
- `sensor.energy_charts_{country}_fossil_brown_coal_lignite` - Brown coal/lignite
- And more depending on country...

### Aggregated Sensors

- `sensor.energy_charts_{country}_total_production` - Total energy production
- `sensor.energy_charts_{country}_renewable_production` - Total renewable production
- `sensor.energy_charts_{country}_renewable_share` - Renewable percentage (%)
- `sensor.energy_charts_{country}_fossil_production` - Total fossil fuel production
- `sensor.energy_charts_{country}_nuclear_production` - Nuclear production

### Category Sensors

- `sensor.energy_charts_{country}_solar_total` - All solar sources combined
- `sensor.energy_charts_{country}_wind_total` - Onshore + offshore wind
- `sensor.energy_charts_{country}_hydro_total` - All hydro sources combined
- `sensor.energy_charts_{country}_fossil_total` - All fossil fuels combined

## Sensor Attributes

Each sensor provides additional attributes:

### Individual Source Sensors
```yaml
state: 35420.5
unit_of_measurement: MW
attributes:
  source_id: photovoltaic
  source_name_en: Photovoltaic
  source_name_de: Photovoltaik
  color: "#FFCC00"
  category: renewable
  last_value_timestamp: "2025-11-01T12:45:00"
  data_source: Fraunhofer ISE Energy-Charts
  country: DE
  daily_peak: 38200.0  # If historical data enabled
  daily_average: 25300.0  # If historical data enabled
```

### Aggregated Sensors
```yaml
state: 115678.9
unit_of_measurement: MW
attributes:
  source_count: 15
  top_5_sources:
    - ["Wind Onshore", 42300.5]
    - ["Solar", 35420.5]
    - ["Gas", 18200.0]
    - ["Nuclear", 12105.3]
    - ["Wind Offshore", 8750.2]
```

### Renewable Share Sensor
```yaml
state: 67.8
unit_of_measurement: "%"
attributes:
  renewable_mw: 78450.2
  total_mw: 115678.9
```

## Example Dashboards

### Energy Production Card (ApexCharts)

> **Note:** This example requires the [ApexCharts Card](https://github.com/RomRider/apexcharts-card) custom card to be installed.

```yaml
type: custom:apexcharts-card
header:
  title: Energy Production Germany
  show: true
series:
  - entity: sensor.energy_charts_germany_solar_total
    name: Solar
    color: yellow
  - entity: sensor.energy_charts_germany_wind_total
    name: Wind
    color: blue
  - entity: sensor.energy_charts_germany_fossil_total
    name: Fossil
    color: gray
  - entity: sensor.energy_charts_germany_nuclear_production
    name: Nuclear
    color: red
```

### Renewable Share Gauge

```yaml
type: gauge
entity: sensor.energy_charts_germany_renewable_share
name: Renewable Energy
unit: "%"
min: 0
max: 100
severity:
  green: 50
  yellow: 30
  red: 0
```

### Energy Statistics Card

```yaml
type: entities
title: Energy Overview
entities:
  - entity: sensor.energy_charts_germany_total_production
    name: Total Production
  - entity: sensor.energy_charts_germany_renewable_production
    name: Renewables
  - entity: sensor.energy_charts_germany_renewable_share
    name: Renewable Share
  - entity: sensor.energy_charts_germany_fossil_production
    name: Fossil Fuels
  - entity: sensor.energy_charts_germany_nuclear_production
    name: Nuclear
```

## Example Automations

### High Renewable Share Alert

```yaml
automation:
  - alias: "Energy: High Renewable Share Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.energy_charts_germany_renewable_share
        above: 80
    action:
      - service: notify.mobile_app
        data:
          title: "Green Energy Alert"
          message: "Currently {{ states('sensor.energy_charts_germany_renewable_share') }}% renewable energy!"
```

### Start Devices During High Solar Production

```yaml
automation:
  - alias: "Energy: Start Dishwasher on High Solar"
    trigger:
      - platform: numeric_state
        entity_id: sensor.energy_charts_germany_solar_total
        above: 30000  # 30 GW
    condition:
      - condition: time
        after: "11:00:00"
        before: "15:00:00"
    action:
      - service: switch.turn_on
        entity_id: switch.dishwasher
```

### Low Fossil Production Logger

```yaml
automation:
  - alias: "Energy: Low Fossil Production Logger"
    trigger:
      - platform: numeric_state
        entity_id: sensor.energy_charts_germany_fossil_total
        below: 10000  # 10 GW
        for:
          hours: 1
    action:
      - service: logbook.log
        data:
          name: "Energy Milestone"
          message: "Fossil fuel production below 10 GW for 1 hour!"
```

## Supported Countries

- 🇩🇪 **Germany (de)** - Full data coverage
- 🇦🇹 **Austria (at)**
- 🇨🇭 **Switzerland (ch)**
- 🇫🇷 **France (fr)**
- 🇳🇱 **Netherlands (nl)**
- 🇧🇪 **Belgium (be)**
- 🇵🇱 **Poland (pl)**
- 🇨🇿 **Czech Republic (cz)**

## Data Source

All data is provided by:
- **Fraunhofer ISE** - Fraunhofer Institute for Solar Energy Systems
- **Energy-Charts**: https://energy-charts.info
- **License**: Public data for non-commercial use

## Troubleshooting

### Integration Not Loading

1. Check Home Assistant logs for errors: **Settings** → **System** → **Logs**
2. Verify the integration files are in the correct location
3. Restart Home Assistant
4. Check that `pydantic>=2.0.0` is available

### No Data / Sensors Show "Unknown"

1. Check your internet connection
2. Verify the Energy-Charts API is accessible: https://www.energy-charts.info
3. Try increasing the update interval in the integration options
4. Check Home Assistant logs for API errors

### Sensors Missing

1. Go to **Settings** → **Devices & Services**
2. Click on the Energy-Charts integration
3. Click **Configure**
4. Verify sensor types are enabled in the configuration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Fraunhofer ISE](https://www.ise.fraunhofer.de/) for providing the Energy-Charts API
- [Energy-Charts](https://energy-charts.info) for the excellent data visualization platform
- The Home Assistant community for inspiration and support

## Disclaimer

**Important Notice:**

- This is an **unofficial integration** and is **not affiliated with, endorsed by, or connected to** Fraunhofer ISE or Energy-Charts in any way.
- This integration is an independent community project that utilizes the publicly available Energy-Charts API.
- **AI-Generated Code**: This integration was developed with the assistance of AI (Claude). While the code has been reviewed and validated, users should be aware of this development method.
- The integration is provided "as is" without warranty of any kind. Use at your own risk.
- Data accuracy depends on the Energy-Charts API and may vary or be unavailable at times.

For official information about Energy-Charts, please visit:
- Official Website: https://energy-charts.info
- Fraunhofer ISE: https://www.ise.fraunhofer.de/

---

**Made with ❤️ for the Home Assistant community**
