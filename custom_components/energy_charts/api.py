"""API Client for Energy-Charts."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_TIMEOUT
from .models import EnergyChartsResponse

_LOGGER = logging.getLogger(__name__)


class EnergyChartsConnectionError(Exception):
    """Exception raised when connection to API fails."""


class EnergyChartsDataError(Exception):
    """Exception raised when API returns invalid data."""


class EnergyChartsTimeoutError(Exception):
    """Exception raised when API request times out."""


class EnergyChartsNotFoundError(Exception):
    """Exception raised when requested resource is not found."""


class EnergyChartsApiClient:
    """Async API Client for Energy-Charts."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        country: str = "de",
    ) -> None:
        """Initialize the API client.

        Args:
            session: aiohttp ClientSession for making requests
            country: Country code (de, at, ch, fr, nl, be, pl, cz)

        """
        self._session = session
        self._country = country.lower()
        self._base_url = API_BASE_URL

    async def _make_request(
        self,
        endpoint: str,
        retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> list[dict[str, Any]]:
        """Make an API request with retry logic.

        Args:
            endpoint: API endpoint (e.g., "day.json")
            retries: Number of retry attempts
            backoff_factor: Exponential backoff factor

        Returns:
            Raw API response data

        Raises:
            EnergyChartsConnectionError: Connection failed
            EnergyChartsTimeoutError: Request timed out
            EnergyChartsNotFoundError: Resource not found (404)
            EnergyChartsDataError: Invalid data received

        """
        url = f"{self._base_url}/{self._country}/{endpoint}"
        last_exception: Exception | None = None

        for attempt in range(retries):
            try:
                timeout = aiohttp.ClientTimeout(total=API_TIMEOUT * (attempt + 1))

                _LOGGER.debug(
                    "Making request to %s (attempt %d/%d)",
                    url,
                    attempt + 1,
                    retries,
                )

                async with self._session.get(url, timeout=timeout) as response:
                    if response.status == 404:
                        raise EnergyChartsNotFoundError(
                            f"Resource not found: {url}"
                        )

                    response.raise_for_status()

                    data = await response.json()

                    if not isinstance(data, list):
                        raise EnergyChartsDataError(
                            f"Expected list, got {type(data).__name__}"
                        )

                    _LOGGER.debug(
                        "Successfully fetched data from %s (%d series)",
                        url,
                        len(data),
                    )
                    return data

            except asyncio.TimeoutError as err:
                last_exception = EnergyChartsTimeoutError(
                    f"Request to {url} timed out"
                )
                _LOGGER.warning(
                    "Timeout on attempt %d/%d: %s",
                    attempt + 1,
                    retries,
                    err,
                )

            except aiohttp.ClientError as err:
                last_exception = EnergyChartsConnectionError(
                    f"Connection error: {err}"
                )
                _LOGGER.warning(
                    "Connection error on attempt %d/%d: %s",
                    attempt + 1,
                    retries,
                    err,
                )

            except EnergyChartsNotFoundError:
                # Don't retry on 404
                raise

            except Exception as err:
                last_exception = EnergyChartsDataError(f"Unexpected error: {err}")
                _LOGGER.warning(
                    "Error on attempt %d/%d: %s",
                    attempt + 1,
                    retries,
                    err,
                )

            # Wait before retrying (exponential backoff)
            if attempt < retries - 1:
                wait_time = backoff_factor * (2**attempt)
                _LOGGER.debug("Waiting %.1f seconds before retry", wait_time)
                await asyncio.sleep(wait_time)

        # All retries exhausted
        if last_exception:
            raise last_exception

        raise EnergyChartsConnectionError("Failed to fetch data after all retries")

    async def get_current_day(self) -> EnergyChartsResponse:
        """Get current day/week data.

        Note: The API doesn't have a 'day.json' endpoint. This method returns
        the current week's data as the most granular real-time data available.

        Returns:
            Parsed Energy Charts response with current week data

        Raises:
            EnergyChartsConnectionError: Connection failed
            EnergyChartsTimeoutError: Request timed out
            EnergyChartsDataError: Invalid data received

        """
        # Use current week data since there's no daily endpoint
        now = datetime.now()
        year, week, _ = now.isocalendar()
        data = await self._make_request(f"week_{year}_{week:02d}.json")
        return EnergyChartsResponse.from_api_response(data)

    async def get_current_week(self) -> EnergyChartsResponse:
        """Get current week data.

        Returns:
            Parsed Energy Charts response with current week data

        Raises:
            EnergyChartsConnectionError: Connection failed
            EnergyChartsTimeoutError: Request timed out
            EnergyChartsDataError: Invalid data received

        """
        now = datetime.now()
        year, week, _ = now.isocalendar()
        data = await self._make_request(f"week_{year}_{week:02d}.json")
        return EnergyChartsResponse.from_api_response(data)

    async def get_current_month(self) -> EnergyChartsResponse:
        """Get current month data.

        Returns:
            Parsed Energy Charts response with current month data

        Raises:
            EnergyChartsConnectionError: Connection failed
            EnergyChartsTimeoutError: Request timed out
            EnergyChartsDataError: Invalid data received

        """
        now = datetime.now()
        year = now.year
        month = now.month
        data = await self._make_request(f"month_{year}_{month:02d}.json")
        return EnergyChartsResponse.from_api_response(data)

    async def get_specific_week(self, year: int, week: int) -> EnergyChartsResponse:
        """Get data for a specific week.

        Args:
            year: Year (e.g., 2025)
            week: ISO week number (1-53)

        Returns:
            Parsed Energy Charts response for the specified week

        Raises:
            EnergyChartsConnectionError: Connection failed
            EnergyChartsTimeoutError: Request timed out
            EnergyChartsNotFoundError: Week not found
            EnergyChartsDataError: Invalid data received

        """
        data = await self._make_request(f"week_{year}_{week:02d}.json")
        return EnergyChartsResponse.from_api_response(data)

    async def get_specific_month(self, year: int, month: int) -> EnergyChartsResponse:
        """Get data for a specific month.

        Args:
            year: Year (e.g., 2025)
            month: Month number (1-12)

        Returns:
            Parsed Energy Charts response for the specified month

        Raises:
            EnergyChartsConnectionError: Connection failed
            EnergyChartsTimeoutError: Request timed out
            EnergyChartsNotFoundError: Month not found
            EnergyChartsDataError: Invalid data received

        """
        data = await self._make_request(f"month_{year}_{month:02d}.json")
        return EnergyChartsResponse.from_api_response(data)

    async def test_connection(self) -> bool:
        """Test if the API is reachable and responding.

        Returns:
            True if connection is successful, False otherwise

        """
        try:
            await self.get_current_day()
            return True
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False
