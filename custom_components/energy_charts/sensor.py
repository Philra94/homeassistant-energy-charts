"""Sensor platform for Energy-Charts integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_API_URL,
    ATTR_CATEGORY,
    ATTR_COLOR,
    ATTR_COUNTRY,
    ATTR_DAILY_AVERAGE,
    ATTR_DAILY_PEAK,
    ATTR_DATA_SOURCE,
    ATTR_HISTORY_TODAY,
    ATTR_LAST_VALUE_TIMESTAMP,
    ATTR_SOURCE_ID,
    ATTR_SOURCE_NAME_DE,
    ATTR_SOURCE_NAME_EN,
    CONF_COUNTRY,
    CONF_ENABLE_AGGREGATED,
    CONF_ENABLE_CATEGORIES,
    CONF_ENABLE_INDIVIDUAL,
    DATA_SOURCE_ATTRIBUTION,
    DATA_SOURCE_URL,
    DEVICE_CLASS_POWER,
    DOMAIN,
    SENSOR_FOSSIL_TOTAL,
    SENSOR_HYDRO_TOTAL,
    SENSOR_RENEWABLE_SHARE,
    SENSOR_SOLAR_TOTAL,
    SENSOR_TOTAL_FOSSIL,
    SENSOR_TOTAL_NUCLEAR,
    SENSOR_TOTAL_PRODUCTION,
    SENSOR_TOTAL_RENEWABLE,
    SENSOR_WIND_TOTAL,
    SOURCE_ICONS,
    STATE_CLASS_MEASUREMENT,
    SUPPORTED_COUNTRIES,
    UNIT_MEGAWATT,
    UNIT_PERCENT,
)
from .coordinator import EnergyChartsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Energy-Charts sensors from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities

    """
    coordinator: EnergyChartsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    country = entry.data[CONF_COUNTRY]

    entities: list[SensorEntity] = []

    # Individual source sensors
    if entry.data.get(CONF_ENABLE_INDIVIDUAL, True):
        # Wait for first data update
        await coordinator.async_config_entry_first_refresh()

        for source_key in coordinator.data.get("sources", {}).keys():
            entities.append(
                EnergyChartsSourceSensor(
                    coordinator=coordinator,
                    entry=entry,
                    source_key=source_key,
                )
            )

    # Aggregated sensors
    if entry.data.get(CONF_ENABLE_AGGREGATED, True):
        entities.extend(
            [
                EnergyChartsTotalProductionSensor(coordinator, entry),
                EnergyChartsTotalRenewableSensor(coordinator, entry),
                EnergyChartsRenewableShareSensor(coordinator, entry),
                EnergyChartsTotalFossilSensor(coordinator, entry),
                EnergyChartsTotalNuclearSensor(coordinator, entry),
            ]
        )

    # Category sensors
    if entry.data.get(CONF_ENABLE_CATEGORIES, True):
        entities.extend(
            [
                EnergyChartsSolarTotalSensor(coordinator, entry),
                EnergyChartsWindTotalSensor(coordinator, entry),
                EnergyChartsHydroTotalSensor(coordinator, entry),
                EnergyChartsFossilTotalSensor(coordinator, entry),
            ]
        )

    async_add_entities(entities)


class EnergyChartsBaseSensor(CoordinatorEntity[EnergyChartsDataUpdateCoordinator], SensorEntity):
    """Base class for Energy-Charts sensors."""

    _attr_attribution = DATA_SOURCE_ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry

        """
        super().__init__(coordinator)
        self._entry = entry
        self._country = entry.data[CONF_COUNTRY]
        self._country_name = SUPPORTED_COUNTRIES.get(self._country, self._country.upper())

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Energy Charts {self._country_name}",
            manufacturer="Fraunhofer ISE",
            model="Energy-Charts API",
            sw_version="1.0",
            configuration_url=DATA_SOURCE_URL,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        # Generate current API URL dynamically
        now = datetime.now()
        year, week, _ = now.isocalendar()
        api_url = f"https://www.energy-charts.info/charts/power/data/{self._country}/week_{year}_{week:02d}.json"

        return {
            ATTR_DATA_SOURCE: DATA_SOURCE_ATTRIBUTION,
            ATTR_COUNTRY: self._country.upper(),
            ATTR_API_URL: api_url,
        }


class EnergyChartsSourceSensor(EnergyChartsBaseSensor):
    """Sensor for individual energy source."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
        source_key: str,
    ) -> None:
        """Initialize the source sensor.

        Args:
            coordinator: Data update coordinator
            entry: Config entry
            source_key: Source key (e.g., "solar", "wind_onshore")

        """
        super().__init__(coordinator, entry)
        self._source_key = source_key

        # Set unique ID
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{source_key}"

        # Set icon based on source type
        icon_key = source_key
        for key in SOURCE_ICONS:
            if key in source_key:
                icon_key = key
                break
        self._attr_icon = SOURCE_ICONS.get(icon_key, "mdi:flash")

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        source_data = self.coordinator.data.get("sources", {}).get(self._source_key, {})
        name = source_data.get("name_en", self._source_key.replace("_", " ").title())
        return name

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        source_data = self.coordinator.data.get("sources", {}).get(self._source_key, {})
        value = source_data.get("value")
        if value is not None:
            return round(value, 2)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        source_data = self.coordinator.data.get("sources", {}).get(self._source_key, {})

        attrs.update(
            {
                ATTR_SOURCE_ID: self._source_key,
                ATTR_SOURCE_NAME_EN: source_data.get("name_en", ""),
                ATTR_SOURCE_NAME_DE: source_data.get("name_de", ""),
                ATTR_COLOR: source_data.get("color", ""),
                ATTR_CATEGORY: source_data.get("category", ""),
            }
        )

        # Add timestamp if available
        timestamp = source_data.get("timestamp")
        if timestamp:
            attrs[ATTR_LAST_VALUE_TIMESTAMP] = timestamp.isoformat()

        # Add historical data if available
        history = self.coordinator.data.get("history", {}).get(self._source_key, [])
        if history:
            # Calculate daily statistics
            values = [val for _, val in history]
            if values:
                attrs[ATTR_DAILY_PEAK] = round(max(values), 2)
                attrs[ATTR_DAILY_AVERAGE] = round(sum(values) / len(values), 2)
                # Store recent history (last 10 points)
                attrs[ATTR_HISTORY_TODAY] = [
                    (ts.isoformat(), round(val, 2)) for ts, val in history[-10:]
                ]

        return attrs


class EnergyChartsTotalProductionSensor(EnergyChartsBaseSensor):
    """Sensor for total energy production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:transmission-tower"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_TOTAL_PRODUCTION}"
        self._attr_name = "Total Production"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("aggregated", {}).get(SENSOR_TOTAL_PRODUCTION)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        sources = self.coordinator.data.get("sources", {})
        source_count = len([s for s in sources.values() if s.get("value", 0) > 0])

        # Get top 5 sources
        sources_with_values = [
            (data.get("name_en", key), data.get("value", 0))
            for key, data in sources.items()
            if data.get("value", 0) > 0
        ]
        top_sources = sorted(sources_with_values, key=lambda x: x[1], reverse=True)[:5]

        attrs.update(
            {
                "source_count": source_count,
                "top_5_sources": [[name, round(val, 2)] for name, val in top_sources],
            }
        )

        return attrs


class EnergyChartsTotalRenewableSensor(EnergyChartsBaseSensor):
    """Sensor for total renewable energy production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:leaf"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_TOTAL_RENEWABLE}"
        self._attr_name = "Renewable Production"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("aggregated", {}).get(SENSOR_TOTAL_RENEWABLE)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        sources = self.coordinator.data.get("sources", {})
        renewable_sources = [
            (data.get("name_en", key), data.get("value", 0))
            for key, data in sources.items()
            if data.get("category") == "renewable" and data.get("value", 0) > 0
        ]

        total_production = self.coordinator.data.get("aggregated", {}).get(
            SENSOR_TOTAL_PRODUCTION, 0
        )
        renewable_total = self.coordinator.data.get("aggregated", {}).get(
            SENSOR_TOTAL_RENEWABLE, 0
        )

        share = 0.0
        if total_production > 0:
            share = (renewable_total / total_production) * 100

        attrs.update(
            {
                "sources": [name for name, _ in renewable_sources],
                "share_of_total": round(share, 2),
            }
        )

        return attrs


class EnergyChartsRenewableShareSensor(EnergyChartsBaseSensor):
    """Sensor for renewable energy share percentage."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_PERCENT
    _attr_icon = "mdi:percent"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_RENEWABLE_SHARE}"
        self._attr_name = "Renewable Share"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("aggregated", {}).get(SENSOR_RENEWABLE_SHARE)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        renewable_mw = self.coordinator.data.get("aggregated", {}).get(
            SENSOR_TOTAL_RENEWABLE, 0
        )
        total_mw = self.coordinator.data.get("aggregated", {}).get(
            SENSOR_TOTAL_PRODUCTION, 0
        )

        attrs.update(
            {
                "renewable_mw": round(renewable_mw, 2),
                "total_mw": round(total_mw, 2),
            }
        )

        return attrs


class EnergyChartsTotalFossilSensor(EnergyChartsBaseSensor):
    """Sensor for total fossil fuel production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:factory"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_TOTAL_FOSSIL}"
        self._attr_name = "Fossil Production"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("aggregated", {}).get(SENSOR_TOTAL_FOSSIL)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        sources = self.coordinator.data.get("sources", {})

        # Get individual fossil fuel types
        coal_mw = sum(
            data.get("value", 0)
            for key, data in sources.items()
            if "coal" in key and data.get("value", 0) > 0
        )
        gas_mw = sum(
            data.get("value", 0)
            for key, data in sources.items()
            if "gas" in key and data.get("value", 0) > 0
        )
        oil_mw = sum(
            data.get("value", 0)
            for key, data in sources.items()
            if "oil" in key and data.get("value", 0) > 0
        )

        attrs.update(
            {
                "coal_mw": round(coal_mw, 2),
                "gas_mw": round(gas_mw, 2),
                "oil_mw": round(oil_mw, 2),
            }
        )

        return attrs


class EnergyChartsTotalNuclearSensor(EnergyChartsBaseSensor):
    """Sensor for nuclear energy production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:radioactive"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_TOTAL_NUCLEAR}"
        self._attr_name = "Nuclear Production"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("aggregated", {}).get(SENSOR_TOTAL_NUCLEAR)


class EnergyChartsSolarTotalSensor(EnergyChartsBaseSensor):
    """Sensor for total solar energy production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:solar-power"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_SOLAR_TOTAL}"
        self._attr_name = "Solar Total"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("categories", {}).get(SENSOR_SOLAR_TOTAL)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        sources = self.coordinator.data.get("sources", {})
        pv_mw = sources.get("photovoltaic", {}).get("value", 0) or 0

        attrs["photovoltaic_mw"] = round(pv_mw, 2)

        return attrs


class EnergyChartsWindTotalSensor(EnergyChartsBaseSensor):
    """Sensor for total wind energy production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:wind-turbine"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_WIND_TOTAL}"
        self._attr_name = "Wind Total"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("categories", {}).get(SENSOR_WIND_TOTAL)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        sources = self.coordinator.data.get("sources", {})
        onshore_mw = sources.get("wind_onshore", {}).get("value", 0) or 0
        offshore_mw = sources.get("wind_offshore", {}).get("value", 0) or 0

        total = onshore_mw + offshore_mw
        onshore_share = 0.0
        if total > 0:
            onshore_share = (onshore_mw / total) * 100

        attrs.update(
            {
                "onshore_mw": round(onshore_mw, 2),
                "offshore_mw": round(offshore_mw, 2),
                "onshore_share": round(onshore_share, 2),
            }
        )

        return attrs


class EnergyChartsHydroTotalSensor(EnergyChartsBaseSensor):
    """Sensor for total hydro energy production."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:water"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_HYDRO_TOTAL}"
        self._attr_name = "Hydro Total"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("categories", {}).get(SENSOR_HYDRO_TOTAL)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = super().extra_state_attributes

        sources = self.coordinator.data.get("sources", {})
        run_of_river = sources.get("hydro_run-of-river", {}).get("value", 0) or 0
        reservoir = sources.get("hydro_water_reservoir", {}).get("value", 0) or 0
        pumped = sources.get("hydro_pumped_storage", {}).get("value", 0) or 0

        attrs.update(
            {
                "run_of_river_mw": round(run_of_river, 2),
                "reservoir_mw": round(reservoir, 2),
                "pumped_storage_mw": round(pumped, 2),
            }
        )

        return attrs


class EnergyChartsFossilTotalSensor(EnergyChartsBaseSensor):
    """Sensor for total fossil fuel production (category)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UNIT_MEGAWATT
    _attr_icon = "mdi:factory"

    def __init__(
        self,
        coordinator: EnergyChartsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{self._country}_{SENSOR_FOSSIL_TOTAL}"
        self._attr_name = "Fossil Total"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("categories", {}).get(SENSOR_FOSSIL_TOTAL)
