from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import GymSet, RunSession, SwimSession, User, Workout, WorkoutType
from app.schemas import WorkoutCreate, WorkoutResponse

router = APIRouter(prefix="/workouts", tags=["workouts"])


class WorkoutUpdate(BaseModel):
    """Fields allowed for partial workout updates."""

    model_config = ConfigDict(extra="forbid")

    date: datetime | None = Field(default=None, description="Updated workout date and time")
    duration_min: int | None = Field(default=None, gt=0, description="Updated workout duration in minutes")
    notes: str | None = Field(default=None, description="Updated workout notes")


@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(workout_data: WorkoutCreate, db: Session = Depends(get_db)) -> Workout:
    """Create a workout and any sport-specific related rows in one transaction."""

    user = db.query(User).filter(User.id == workout_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {workout_data.user_id} was not found",
        )

    workout = Workout(
        user_id=workout_data.user_id,
        type=WorkoutType(workout_data.type),
        date=workout_data.date,
        duration_min=workout_data.duration_min,
        notes=workout_data.notes,
    )
    db.add(workout)

    try:
        db.flush()

        if workout.type == WorkoutType.GYM:
            for gym_set_data in workout_data.gym_sets or []:
                db.add(
                    GymSet(
                        workout_id=workout.id,
                        exercise_name=gym_set_data.exercise_name,
                        muscle_group=gym_set_data.muscle_group,
                        sets=gym_set_data.sets,
                        reps=gym_set_data.reps,
                        weight_kg=gym_set_data.weight_kg,
                    )
                )
        elif workout.type == WorkoutType.RUN:
            db.add(
                RunSession(
                    workout_id=workout.id,
                    distance_km=workout_data.run_session.distance_km,
                    avg_pace_min_km=workout_data.run_session.avg_pace_min_km,
                    elevation_m=workout_data.run_session.elevation_m,
                    route_name=workout_data.run_session.route_name,
                )
            )
        elif workout.type == WorkoutType.SWIM:
            db.add(
                SwimSession(
                    workout_id=workout.id,
                    distance_m=workout_data.swim_session.distance_m,
                    pool_length_m=workout_data.swim_session.pool_length_m,
                    strokes=workout_data.swim_session.strokes,
                    avg_heart_rate=workout_data.swim_session.avg_heart_rate,
                )
            )

        db.commit()
        db.refresh(workout)
    except Exception:
        db.rollback()
        raise

    return (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session))
        .filter(Workout.id == workout.id)
        .first()
    )


@router.get("/", response_model=list[WorkoutResponse])
def list_workouts(
    user_id: int | None = Query(default=None),
    type: Literal["gym", "run", "swim"] | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[Workout]:
    """List workouts with optional filters and pagination."""

    query = db.query(Workout).options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session))

    if user_id is not None:
        query = query.filter(Workout.user_id == user_id)
    if type is not None:
        query = query.filter(Workout.type == WorkoutType(type))
    if date_from is not None:
        query = query.filter(Workout.date >= date_from)
    if date_to is not None:
        query = query.filter(Workout.date <= date_to)

    return query.order_by(Workout.date.desc()).offset(skip).limit(limit).all()


@router.get("/{workout_id}", response_model=WorkoutResponse)
def get_workout(workout_id: int, db: Session = Depends(get_db)) -> Workout:
    """Fetch a single workout with nested data."""

    workout = (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session))
        .filter(Workout.id == workout_id)
        .first()
    )
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with id {workout_id} was not found",
        )
    return workout


@router.patch("/{workout_id}", response_model=WorkoutResponse)
def update_workout(
    workout_id: int,
    workout_update: WorkoutUpdate,
    db: Session = Depends(get_db),
) -> Workout:
    """Update top-level workout fields only."""

    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with id {workout_id} was not found",
        )

    update_data = workout_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workout, field, value)

    db.commit()
    db.refresh(workout)

    return (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session))
        .filter(Workout.id == workout.id)
        .first()
    )


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a workout and let the database cascade the related rows."""

    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workout with id {workout_id} was not found",
        )

    db.delete(workout)
    db.commit()
    return None
