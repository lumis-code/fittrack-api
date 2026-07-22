from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SwimSessionBase(BaseModel):
    """Shared swimming workout fields."""

    distance_m: int = Field(..., gt=0, description="Distance covered in meters")
    pool_length_m: int = Field(..., gt=0, description="Length of the pool in meters")
    strokes: int | None = Field(default=None, description="Average stroke count")
    avg_heart_rate: int | None = Field(default=None, description="Average heart rate")


class SwimSessionCreate(SwimSessionBase):
    """Fields accepted when creating a swimming session."""


class SwimSessionResponse(SwimSessionBase):
    """Swimming session representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
