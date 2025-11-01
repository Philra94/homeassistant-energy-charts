"""The Energy-Charts integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EnergyChartsApiClient
from .const import CONF_COUNTRY, DOMAIN
from .coordinator import EnergyChartsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy-Charts from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if setup was successful

    """
    _LOGGER.debug("Setting up Energy-Charts integration for %s", entry.data[CONF_COUNTRY])

    # Create API client
    session = async_get_clientsession(hass)
    api_client = EnergyChartsApiClient(
        session=session,
        country=entry.data[CONF_COUNTRY],
    )

    # Create coordinator
    coordinator = EnergyChartsDataUpdateCoordinator(
        hass=hass,
        entry=entry,
        api_client=api_client,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload was successful

    """
    _LOGGER.debug("Unloading Energy-Charts integration for %s", entry.data[CONF_COUNTRY])

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    """
    _LOGGER.debug("Updating options for %s", entry.data[CONF_COUNTRY])

    # Reload the config entry to apply new options
    await hass.config_entries.async_reload(entry.entry_id)
