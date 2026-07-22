from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GymSetBase(BaseModel):
    """Shared gym exercise fields."""

    exercise_name: str = Field(..., description="Name of the exercise")
    muscle_group: str = Field(..., description="Primary muscle group targeted")
    sets: int = Field(..., gt=0, description="Number of sets")
    reps: int = Field(..., gt=0, description="Repetitions per set")
    weight_kg: float = Field(..., ge=0, description="Weight used in kilograms")


class GymSetCreate(GymSetBase):
    """Fields accepted when creating a gym set entry."""


class GymSetResponse(GymSetBase):
    """Gym set representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
