"""Config flow for Energy-Charts integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyChartsApiClient
from .const import (
    CONF_COUNTRY,
    CONF_ENABLE_AGGREGATED,
    CONF_ENABLE_CATEGORIES,
    CONF_ENABLE_INDIVIDUAL,
    CONF_ENABLE_FORECASTS,
    CONF_HISTORICAL_RANGE,
    CONF_LANGUAGE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_COUNTRY,
    DEFAULT_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    HISTORICAL_RANGE_DAY,
    HISTORICAL_RANGE_MONTH,
    HISTORICAL_RANGE_NONE,
    HISTORICAL_RANGE_WEEK,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    SUPPORTED_COUNTRIES,
    SUPPORTED_LANGUAGES,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(
    hass: HomeAssistant, country: str
) -> dict[str, Any]:
    """Validate the API connection.

    Args:
        hass: Home Assistant instance
        country: Country code

    Returns:
        Dictionary with validation result

    Raises:
        ValueError: If connection fails

    """
    session = async_get_clientsession(hass)
    client = EnergyChartsApiClient(session=session, country=country)

    if not await client.test_connection():
        raise ValueError("Cannot connect to Energy-Charts API")

    return {"title": f"Energy Charts {SUPPORTED_COUNTRIES[country]}"}


class EnergyChartsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy-Charts."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.

        Args:
            user_input: User input data

        Returns:
            Flow result

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            country = user_input[CONF_COUNTRY]

            # Check if already configured
            await self.async_set_unique_id(f"{DOMAIN}_{country}")
            self._abort_if_unique_id_configured()

            try:
                info = await validate_connection(self.hass, country)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during connection test")
                errors["base"] = "unknown"
            else:
                # Store data for next step
                self._data = user_input
                return await self.async_step_sensors()

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_COUNTRY, default=DEFAULT_COUNTRY): vol.In(
                    SUPPORTED_COUNTRIES
                ),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle sensor selection step.

        Args:
            user_input: User input data

        Returns:
            Flow result

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Merge with previous data
            self._data.update(user_input)

            # Validate at least one sensor type is enabled
            if not any(
                [
                    user_input.get(CONF_ENABLE_INDIVIDUAL, True),
                    user_input.get(CONF_ENABLE_AGGREGATED, True),
                    user_input.get(CONF_ENABLE_CATEGORIES, True),
                ]
            ):
                errors["base"] = "no_sensors_selected"
            else:
                return await self.async_step_advanced()

        # Show form
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_ENABLE_INDIVIDUAL, default=True): bool,
                vol.Optional(CONF_ENABLE_AGGREGATED, default=True): bool,
                vol.Optional(CONF_ENABLE_CATEGORIES, default=True): bool,
                vol.Optional(CONF_ENABLE_FORECASTS, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="sensors",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle advanced options step.

        Args:
            user_input: User input data

        Returns:
            Flow result

        """
        if user_input is not None:
            # Merge with previous data
            self._data.update(user_input)

            # Create config entry
            country = self._data[CONF_COUNTRY]
            country_name = SUPPORTED_COUNTRIES[country]

            return self.async_create_entry(
                title=f"Energy Charts {country_name}",
                data=self._data,
            )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_HISTORICAL_RANGE, default=HISTORICAL_RANGE_DAY): vol.In(
                    {
                        HISTORICAL_RANGE_NONE: "None",
                        HISTORICAL_RANGE_DAY: "Day",
                        HISTORICAL_RANGE_WEEK: "Week",
                        HISTORICAL_RANGE_MONTH: "Month",
                    }
                ),
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(
                    SUPPORTED_LANGUAGES
                ),
            }
        )

        return self.async_show_form(
            step_id="advanced",
            data_schema=data_schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EnergyChartsOptionsFlow:
        """Get the options flow.

        Args:
            config_entry: Config entry

        Returns:
            Options flow handler

        """
        return EnergyChartsOptionsFlow(config_entry)


class EnergyChartsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Energy-Charts."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        Args:
            config_entry: Config entry

        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.

        Args:
            user_input: User input data

        Returns:
            Flow result

        """
        if user_input is not None:
            # Update config entry with new options
            return self.async_create_entry(title="", data=user_input)

        # Get current values
        current_data = self.config_entry.data

        # Show form with current values
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=current_data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)),
                vol.Optional(
                    CONF_ENABLE_INDIVIDUAL,
                    default=current_data.get(CONF_ENABLE_INDIVIDUAL, True),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_AGGREGATED,
                    default=current_data.get(CONF_ENABLE_AGGREGATED, True),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_CATEGORIES,
                    default=current_data.get(CONF_ENABLE_CATEGORIES, True),
                ): bool,
                vol.Optional(
                    CONF_ENABLE_FORECASTS,
                    default=current_data.get(CONF_ENABLE_FORECASTS, False),
                ): bool,
                vol.Optional(
                    CONF_HISTORICAL_RANGE,
                    default=current_data.get(CONF_HISTORICAL_RANGE, HISTORICAL_RANGE_DAY),
                ): vol.In(
                    {
                        HISTORICAL_RANGE_NONE: "None",
                        HISTORICAL_RANGE_DAY: "Day",
                        HISTORICAL_RANGE_WEEK: "Week",
                        HISTORICAL_RANGE_MONTH: "Month",
                    }
                ),
                vol.Optional(
                    CONF_LANGUAGE,
                    default=current_data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                ): vol.In(SUPPORTED_LANGUAGES),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
