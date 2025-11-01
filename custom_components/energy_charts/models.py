"""Data models for Energy-Charts API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EnergyDataSeries(BaseModel):
    """Represents a single energy data series from the API."""

    name: dict[str, str] = Field(..., description="Multilingual name dictionary")
    color: str = Field(..., description="RGB color code")
    data: list[float | None] = Field(
        default_factory=list, description="Time series data values"
    )
    timestamps: list[int] = Field(
        default_factory=list, description="Unix timestamps in milliseconds"
    )
    visible: bool = Field(default=True, description="Whether series is visible")

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: dict | list) -> dict:
        """Normalize name field - handle both dict and list[dict] formats.

        The API inconsistently returns name as either:
        - dict: {"en": "...", "de": "...", ...}
        - list: [{"en": "...", "de": "...", ...}]

        This validator normalizes to always return a dict.
        """
        if isinstance(v, list) and len(v) > 0:
            return v[0]
        if isinstance(v, dict):
            return v
        return {}

    class Config:
        """Pydantic config."""

        populate_by_name = True

    @property
    def name_en(self) -> str:
        """Get English name."""
        return self.name.get("en", "Unknown")

    @property
    def name_de(self) -> str:
        """Get German name."""
        return self.name.get("de", "Unbekannt")

    @property
    def key(self) -> str:
        """Generate a unique key from the English name."""
        # Convert name to snake_case key
        name = self.name_en.lower()
        # Replace special characters and spaces
        key = (
            name.replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(",", "")
        )
        # Remove duplicate underscores
        while "__" in key:
            key = key.replace("__", "_")
        return key.strip("_")

    @property
    def latest_value(self) -> float | None:
        """Get the most recent non-null value."""
        for value in reversed(self.data):
            if value is not None:
                return float(value)
        return None

    @property
    def latest_timestamp(self) -> datetime | None:
        """Get the timestamp of the most recent non-null value."""
        if not self.timestamps or not self.data:
            return None

        # Find the last non-null value and its index
        for i in range(len(self.data) - 1, -1, -1):
            if self.data[i] is not None and i < len(self.timestamps):
                return datetime.fromtimestamp(self.timestamps[i] / 1000)
        return None

    def get_values_as_dict(self) -> dict[datetime, float]:
        """Convert data to dict with datetime keys and float values."""
        result = {}
        for i, value in enumerate(self.data):
            if value is not None and i < len(self.timestamps):
                timestamp = datetime.fromtimestamp(self.timestamps[i] / 1000)
                result[timestamp] = float(value)
        return result

    def get_data_points(self) -> list[tuple[datetime, float]]:
        """Get data as list of (timestamp, value) tuples."""
        result = []
        for i, value in enumerate(self.data):
            if value is not None and i < len(self.timestamps):
                timestamp = datetime.fromtimestamp(self.timestamps[i] / 1000)
                result.append((timestamp, float(value)))
        return result


class EnergyChartsResponse(BaseModel):
    """Complete response from Energy-Charts API."""

    data_series: list[EnergyDataSeries] = Field(
        default_factory=list, description="List of energy data series"
    )

    @classmethod
    def from_api_response(cls, response_data: list[dict[str, Any]]) -> EnergyChartsResponse:
        """Create instance from raw API response.

        The API returns an array of series objects. The first object contains
        xAxisValues (timestamps) that apply to all series.
        """
        if not response_data:
            return cls(data_series=[])

        # Extract timestamps from the first item (they apply to all series)
        timestamps = response_data[0].get("xAxisValues", [])

        # Parse each series
        data_series = []
        for item in response_data:
            # Skip items without name or data
            if "name" not in item or "data" not in item:
                continue

            # Create series with timestamps
            series = EnergyDataSeries(
                name=item["name"],
                color=item.get("color", "#000000"),
                data=item.get("data", []),
                timestamps=timestamps,
                visible=item.get("visible", True),
            )
            data_series.append(series)

        return cls(data_series=data_series)

    def get_series_by_key(self, key: str) -> EnergyDataSeries | None:
        """Get a specific data series by its key."""
        for series in self.data_series:
            if series.key == key:
                return series
        return None

    def get_series_by_name(self, name: str, language: str = "en") -> EnergyDataSeries | None:
        """Get a specific data series by its name."""
        for series in self.data_series:
            if series.name.get(language, "").lower() == name.lower():
                return series
        return None

    def get_series_keys(self) -> list[str]:
        """Get all available data series keys."""
        return [series.key for series in self.data_series]


class CoordinatorData(BaseModel):
    """Structured data provided by the coordinator to sensors."""

    timestamp: datetime = Field(default_factory=datetime.now)
    raw_response: EnergyChartsResponse
    sources: dict[str, dict[str, Any]] = Field(default_factory=dict)
    aggregated: dict[str, float] = Field(default_factory=dict)
    categories: dict[str, float] = Field(default_factory=dict)
    history: dict[str, list[tuple[datetime, float]]] = Field(default_factory=dict)
    forecasts: dict[str, list[tuple[datetime, float]]] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
