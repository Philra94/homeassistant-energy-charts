"""DataUpdateCoordinator for Energy-Charts integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    EnergyChartsApiClient,
    EnergyChartsConnectionError,
    EnergyChartsDataError,
    EnergyChartsTimeoutError,
)
from .const import (
    CATEGORY_FOSSIL,
    CATEGORY_NUCLEAR,
    CATEGORY_RENEWABLE,
    CONF_COUNTRY,
    CONF_HISTORICAL_RANGE,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    FOSSIL_SOURCES,
    HISTORICAL_RANGE_NONE,
    NUCLEAR_SOURCES,
    RENEWABLE_SOURCES,
    SENSOR_FOSSIL_TOTAL,
    SENSOR_HYDRO_TOTAL,
    SENSOR_RENEWABLE_SHARE,
    SENSOR_SOLAR_TOTAL,
    SENSOR_TOTAL_FOSSIL,
    SENSOR_TOTAL_NUCLEAR,
    SENSOR_TOTAL_PRODUCTION,
    SENSOR_TOTAL_RENEWABLE,
    SENSOR_WIND_TOTAL,
    SOURCE_CATEGORIES,
)
from .models import CoordinatorData, EnergyChartsResponse

_LOGGER = logging.getLogger(__name__)


class EnergyChartsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Energy-Charts data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api_client: EnergyChartsApiClient,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            entry: Config entry
            api_client: API client instance

        """
        self.api_client = api_client
        self.entry = entry
        self.country = entry.data[CONF_COUNTRY]

        update_interval = timedelta(
            minutes=entry.data.get(CONF_UPDATE_INTERVAL, 15)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.country}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API.

        Returns:
            Structured data dictionary for sensors

        Raises:
            UpdateFailed: When update fails

        """
        try:
            # Fetch current day data
            response = await self.api_client.get_current_day()

            # Process and structure the data
            structured_data = self._process_response(response)

            # Optionally fetch historical data
            historical_range = self.entry.data.get(CONF_HISTORICAL_RANGE, HISTORICAL_RANGE_NONE)
            if historical_range != HISTORICAL_RANGE_NONE:
                structured_data["history"] = await self._fetch_historical_data(
                    historical_range
                )

            return structured_data

        except EnergyChartsConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except EnergyChartsTimeoutError as err:
            raise UpdateFailed(f"Timeout error: {err}") from err
        except EnergyChartsDataError as err:
            raise UpdateFailed(f"Data error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _process_response(self, response: EnergyChartsResponse) -> dict[str, Any]:
        """Process API response into structured data.

        Args:
            response: API response object

        Returns:
            Structured data dictionary

        """
        data: dict[str, Any] = {
            "timestamp": datetime.now(),
            "raw_response": response,
            "sources": {},
            "aggregated": {},
            "categories": {},
            "history": {},
            "forecasts": {},
        }

        # Process individual sources
        for series in response.data_series:
            source_key = series.key.lower()

            # Skip forecast series for now (they typically have "_planned" suffix)
            if "_planned" in source_key or "forecast" in source_key:
                continue

            source_data = {
                "value": series.latest_value,
                "unit": "MW",
                "timestamp": series.latest_timestamp,
                "name_en": series.name_en,
                "name_de": series.name_de,
                "color": series.color,
                "category": SOURCE_CATEGORIES.get(source_key, "other"),
                "key": source_key,
            }

            data["sources"][source_key] = source_data

        # Calculate aggregated values
        data["aggregated"] = self._calculate_aggregated(data["sources"])

        # Calculate category sums
        data["categories"] = self._calculate_categories(data["sources"])

        return data

    def _calculate_aggregated(
        self, sources: dict[str, dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate aggregated sensor values.

        Args:
            sources: Dictionary of source data

        Returns:
            Dictionary of aggregated values

        """
        aggregated: dict[str, float] = {}

        # Total production (sum of all positive values)
        total_production = 0.0
        total_renewable = 0.0
        total_fossil = 0.0
        total_nuclear = 0.0

        for source_key, source_data in sources.items():
            value = source_data.get("value")
            if value is None:
                continue

            # Only count positive values for production
            if value > 0:
                total_production += value

            category = source_data.get("category")

            if category == CATEGORY_RENEWABLE:
                total_renewable += value
            elif category == CATEGORY_FOSSIL:
                total_fossil += value
            elif category == CATEGORY_NUCLEAR:
                total_nuclear += value

        aggregated[SENSOR_TOTAL_PRODUCTION] = round(total_production, 2)
        aggregated[SENSOR_TOTAL_RENEWABLE] = round(total_renewable, 2)
        aggregated[SENSOR_TOTAL_FOSSIL] = round(total_fossil, 2)
        aggregated[SENSOR_TOTAL_NUCLEAR] = round(total_nuclear, 2)

        # Calculate renewable share
        if total_production > 0:
            renewable_share = (total_renewable / total_production) * 100
            aggregated[SENSOR_RENEWABLE_SHARE] = round(renewable_share, 2)
        else:
            aggregated[SENSOR_RENEWABLE_SHARE] = 0.0

        return aggregated

    def _calculate_categories(
        self, sources: dict[str, dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate category totals.

        Args:
            sources: Dictionary of source data

        Returns:
            Dictionary of category totals

        """
        categories: dict[str, float] = {}

        # Solar total (photovoltaic + solar)
        solar_total = 0.0
        for key in ["photovoltaic", "solar"]:
            if key in sources and sources[key].get("value"):
                solar_total += sources[key]["value"]
        categories[SENSOR_SOLAR_TOTAL] = round(solar_total, 2)

        # Wind total (onshore + offshore)
        wind_total = 0.0
        for key in ["wind_onshore", "wind_offshore"]:
            if key in sources and sources[key].get("value"):
                wind_total += sources[key]["value"]
        categories[SENSOR_WIND_TOTAL] = round(wind_total, 2)

        # Hydro total (run-of-river + reservoir + pumped storage)
        hydro_total = 0.0
        for key in [
            "hydro_run-of-river",
            "hydro_water_reservoir",
            "hydro_pumped_storage",
        ]:
            if key in sources and sources[key].get("value"):
                hydro_total += sources[key]["value"]
        categories[SENSOR_HYDRO_TOTAL] = round(hydro_total, 2)

        # Fossil total
        fossil_total = 0.0
        for key in FOSSIL_SOURCES:
            if key in sources and sources[key].get("value"):
                fossil_total += sources[key]["value"]
        categories[SENSOR_FOSSIL_TOTAL] = round(fossil_total, 2)

        return categories

    async def _fetch_historical_data(
        self, historical_range: str
    ) -> dict[str, list[tuple[datetime, float]]]:
        """Fetch historical data based on configured range.

        Args:
            historical_range: One of "day", "week", "month"

        Returns:
            Dictionary with historical data

        """
        history: dict[str, list[tuple[datetime, float]]] = {}

        try:
            if historical_range == "day":
                response = await self.api_client.get_current_day()
            elif historical_range == "week":
                response = await self.api_client.get_current_week()
            elif historical_range == "month":
                response = await self.api_client.get_current_month()
            else:
                return history

            # Convert to historical format
            for series in response.data_series:
                source_key = series.key.lower()
                history[source_key] = [
                    (datetime.fromtimestamp(ts / 1000), float(val))
                    for ts, val in series.data
                    if val is not None
                ]

        except Exception as err:
            _LOGGER.warning("Failed to fetch historical data: %s", err)

        return history
