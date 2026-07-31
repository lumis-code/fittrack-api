from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CyclingSessionBase(BaseModel):
    """Shared cycling workout fields."""

    distance_km: float = Field(..., gt=0, description="Distance covered in kilometers")
    avg_speed_kmh: float = Field(..., gt=0, description="Average speed in kilometers per hour")
    elevation_m: int | None = Field(default=None, description="Total elevation gain in meters")
    route_name: str | None = Field(default=None, description="Optional route name")


class CyclingSessionCreate(CyclingSessionBase):
    """Fields accepted when creating a cycling session."""


class CyclingSessionResponse(CyclingSessionBase):
    """Cycling session representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
