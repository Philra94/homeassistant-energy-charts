"""Constants for the Energy-Charts integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

# Domain
DOMAIN: Final = "energy_charts"

# Platforms
PLATFORMS: Final = ["sensor"]

# Config
CONF_COUNTRY: Final = "country"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_ENABLE_INDIVIDUAL: Final = "enable_individual_sources"
CONF_ENABLE_AGGREGATED: Final = "enable_aggregated"
CONF_ENABLE_CATEGORIES: Final = "enable_categories"
CONF_ENABLE_FORECASTS: Final = "enable_forecasts"
CONF_HISTORICAL_RANGE: Final = "historical_data_range"
CONF_LANGUAGE: Final = "language"

# Defaults
DEFAULT_COUNTRY: Final = "de"
DEFAULT_UPDATE_INTERVAL: Final = 15
DEFAULT_NAME: Final = "Energy Charts"
DEFAULT_LANGUAGE: Final = "de"

# API
API_BASE_URL: Final = "https://www.energy-charts.info/charts/power/data"
API_TIMEOUT: Final = 30

# Update Intervals
MIN_UPDATE_INTERVAL: Final = 5
MAX_UPDATE_INTERVAL: Final = 60
UPDATE_INTERVAL_DAY: Final = timedelta(minutes=15)
UPDATE_INTERVAL_WEEK: Final = timedelta(minutes=30)
UPDATE_INTERVAL_MONTH: Final = timedelta(minutes=60)

# Countries
SUPPORTED_COUNTRIES: Final = {
    "de": "Germany",
    "at": "Austria",
    "ch": "Switzerland",
    "fr": "France",
    "nl": "Netherlands",
    "be": "Belgium",
    "pl": "Poland",
    "cz": "Czech Republic",
}

# Energy Source Categories
CATEGORY_RENEWABLE: Final = "renewable"
CATEGORY_FOSSIL: Final = "fossil"
CATEGORY_NUCLEAR: Final = "nuclear"
CATEGORY_STORAGE: Final = "storage"
CATEGORY_TRADE: Final = "trade"

# Renewable Sources
RENEWABLE_SOURCES: Final = [
    "hydro_run-of-river",
    "biomass",
    "wind_offshore",
    "wind_onshore",
    "photovoltaic",
    "solar",
    "hydro_water_reservoir",
]

# Fossil Sources
FOSSIL_SOURCES: Final = [
    "fossil_brown_coal_lignite",
    "fossil_brown_coal/lignite",
    "fossil_hard_coal",
    "fossil_coal-derived_gas",
    "fossil_gas",
    "fossil_oil",
]

# Nuclear Sources
NUCLEAR_SOURCES: Final = [
    "nuclear",
]

# Storage Sources
STORAGE_SOURCES: Final = [
    "hydro_pumped_storage",
    "battery",
    "battery_storage",
]

# Source Categories Mapping
SOURCE_CATEGORIES: Final = {
    # Renewable
    "hydro_run-of-river": CATEGORY_RENEWABLE,
    "biomass": CATEGORY_RENEWABLE,
    "wind_offshore": CATEGORY_RENEWABLE,
    "wind_onshore": CATEGORY_RENEWABLE,
    "photovoltaic": CATEGORY_RENEWABLE,
    "solar": CATEGORY_RENEWABLE,
    "hydro_water_reservoir": CATEGORY_RENEWABLE,
    "geothermal": CATEGORY_RENEWABLE,
    # Fossil
    "fossil_brown_coal_lignite": CATEGORY_FOSSIL,
    "fossil_brown_coal/lignite": CATEGORY_FOSSIL,
    "fossil_hard_coal": CATEGORY_FOSSIL,
    "fossil_coal-derived_gas": CATEGORY_FOSSIL,
    "fossil_gas": CATEGORY_FOSSIL,
    "fossil_oil": CATEGORY_FOSSIL,
    # Nuclear
    "nuclear": CATEGORY_NUCLEAR,
    # Storage
    "hydro_pumped_storage": CATEGORY_STORAGE,
    "battery": CATEGORY_STORAGE,
    "battery_storage": CATEGORY_STORAGE,
}

# Icon Mapping
SOURCE_ICONS: Final = {
    "solar": "mdi:solar-power",
    "photovoltaic": "mdi:solar-panel",
    "wind_onshore": "mdi:wind-turbine",
    "wind_offshore": "mdi:wind-turbine",
    "hydro": "mdi:water",
    "hydro_run-of-river": "mdi:water",
    "hydro_water_reservoir": "mdi:water",
    "hydro_pumped_storage": "mdi:water-pump",
    "biomass": "mdi:leaf",
    "nuclear": "mdi:radioactive",
    "fossil_gas": "mdi:fire",
    "fossil_coal": "mdi:factory",
    "fossil_hard_coal": "mdi:factory",
    "fossil_brown_coal_lignite": "mdi:factory",
    "fossil_brown_coal/lignite": "mdi:factory",
    "fossil_oil": "mdi:oil",
    "storage": "mdi:battery",
    "battery": "mdi:battery",
    "battery_storage": "mdi:battery",
    "trade": "mdi:transit-connection-variant",
    "geothermal": "mdi:fire",
}

# Sensor Types
SENSOR_TYPE_SOURCE: Final = "source"
SENSOR_TYPE_AGGREGATED: Final = "aggregated"
SENSOR_TYPE_CATEGORY: Final = "category"
SENSOR_TYPE_FORECAST: Final = "forecast"

# Sensor Keys for Aggregated Sensors
SENSOR_TOTAL_PRODUCTION: Final = "total_production"
SENSOR_TOTAL_RENEWABLE: Final = "total_renewable"
SENSOR_RENEWABLE_SHARE: Final = "renewable_share"
SENSOR_TOTAL_FOSSIL: Final = "total_fossil"
SENSOR_TOTAL_NUCLEAR: Final = "total_nuclear"

# Sensor Keys for Category Sensors
SENSOR_SOLAR_TOTAL: Final = "solar_total"
SENSOR_WIND_TOTAL: Final = "wind_total"
SENSOR_HYDRO_TOTAL: Final = "hydro_total"
SENSOR_FOSSIL_TOTAL: Final = "fossil_total"

# State Classes
STATE_CLASS_MEASUREMENT: Final = "measurement"
STATE_CLASS_TOTAL: Final = "total"

# Device Classes
DEVICE_CLASS_POWER: Final = "power"
DEVICE_CLASS_ENERGY: Final = "energy"

# Units
UNIT_MEGAWATT: Final = "MW"
UNIT_PERCENT: Final = "%"

# Attribute Keys
ATTR_SOURCE_ID: Final = "source_id"
ATTR_SOURCE_NAME_EN: Final = "source_name_en"
ATTR_SOURCE_NAME_DE: Final = "source_name_de"
ATTR_COLOR: Final = "color"
ATTR_CATEGORY: Final = "category"
ATTR_LAST_VALUE_TIMESTAMP: Final = "last_value_timestamp"
ATTR_IS_FORECAST: Final = "is_forecast"
ATTR_HISTORY_TODAY: Final = "history_today"
ATTR_DAILY_PEAK: Final = "daily_peak"
ATTR_DAILY_AVERAGE: Final = "daily_average"
ATTR_DATA_SOURCE: Final = "data_source"
ATTR_COUNTRY: Final = "country"
ATTR_API_URL: Final = "api_url"

# Historical Data Range Options
HISTORICAL_RANGE_NONE: Final = "none"
HISTORICAL_RANGE_DAY: Final = "day"
HISTORICAL_RANGE_WEEK: Final = "week"
HISTORICAL_RANGE_MONTH: Final = "month"

HISTORICAL_RANGE_OPTIONS: Final = [
    HISTORICAL_RANGE_NONE,
    HISTORICAL_RANGE_DAY,
    HISTORICAL_RANGE_WEEK,
    HISTORICAL_RANGE_MONTH,
]

# Language Options
SUPPORTED_LANGUAGES: Final = ["en", "de", "fr", "it", "es"]

# Data Source Attribution
DATA_SOURCE_ATTRIBUTION: Final = "Fraunhofer ISE Energy-Charts"
DATA_SOURCE_URL: Final = "https://energy-charts.info"
