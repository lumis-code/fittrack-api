from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.gym_set import GymSetCreate, GymSetResponse
from app.schemas.run_session import RunSessionCreate, RunSessionResponse
from app.schemas.swim_session import SwimSessionCreate, SwimSessionResponse


class WorkoutBase(BaseModel):
    """Shared workout fields."""

    type: Literal["gym", "run", "swim"] = Field(..., description="Type of workout")
    date: datetime = Field(..., description="Workout date and time")
    duration_min: int = Field(..., gt=0, description="Workout duration in minutes")
    notes: str | None = Field(default=None, description="Optional workout notes")


class WorkoutCreate(WorkoutBase):
    """Fields accepted when creating a workout."""

    user_id: int = Field(..., description="Owner user id")
    gym_sets: list[GymSetCreate] | None = Field(default=None, description="Gym sets for gym workouts")
    run_session: RunSessionCreate | None = Field(default=None, description="Running details for run workouts")
    swim_session: SwimSessionCreate | None = Field(default=None, description="Swimming details for swim workouts")

    @model_validator(mode="after")
    def validate_workout_payload(self) -> "WorkoutCreate":
        if self.type == "gym":
            if not self.gym_sets:
                raise ValueError("gym workouts must include at least one gym_sets entry")
        elif self.type == "run":
            if self.run_session is None:
                raise ValueError("run workouts must include a run_session payload")
        elif self.type == "swim":
            if self.swim_session is None:
                raise ValueError("swim workouts must include a swim_session payload")
        return self


class WorkoutResponse(WorkoutBase):
    """Workout representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    gym_sets: list[GymSetResponse] = []
    run_session: RunSessionResponse | None = None
    swim_session: SwimSessionResponse | None = None
