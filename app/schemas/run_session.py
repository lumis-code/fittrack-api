from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RunSessionBase(BaseModel):
    """Shared running workout fields."""

    distance_km: float = Field(..., gt=0, description="Distance covered in kilometers")
    avg_pace_min_km: float = Field(..., gt=0, description="Average pace in minutes per kilometer")
    elevation_m: int | None = Field(default=None, description="Total elevation gain in meters")
    route_name: str | None = Field(default=None, description="Optional route name")


class RunSessionCreate(RunSessionBase):
    """Fields accepted when creating a running session."""


class RunSessionResponse(RunSessionBase):
    """Running session representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
