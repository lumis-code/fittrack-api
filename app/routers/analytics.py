from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RunSession, SwimSession, User, Workout

router = APIRouter(tags=["analytics"])


class UserStatsResponse(BaseModel):
    """Aggregated statistics for a user."""

    model_config = ConfigDict(from_attributes=True)

    total_workouts: int
    total_duration_hours: float
    total_distance_km: float
    breakdown_by_type: dict[str, int]


class WeeklyStatsResponse(BaseModel):
    """Weekly workout summary for a user."""

    model_config = ConfigDict(from_attributes=True)

    week_start: date
    workout_count: int
    total_duration_min: int


class OverdueUserResponse(BaseModel):
    """Users who have not logged a workout recently."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    last_workout_date: datetime | None = None
    days_since_last_workout: int | None = None


@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
def get_user_stats(user_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return aggregate workout statistics for a user."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} was not found")

    workout_counts = (
        db.query(Workout.type, func.count(Workout.id))
        .filter(Workout.user_id == user_id)
        .group_by(Workout.type)
        .all()
    )
    breakdown_by_type = {"gym": 0, "run": 0, "swim": 0}
    for workout_type, count in workout_counts:
        breakdown_by_type[workout_type.value if hasattr(workout_type, "value") else str(workout_type)] = count

    total_workouts = sum(breakdown_by_type.values())

    total_duration_min = (
        db.query(func.coalesce(func.sum(Workout.duration_min), 0))
        .filter(Workout.user_id == user_id)
        .scalar()
        or 0
    )

    total_run_distance_km = (
        db.query(func.coalesce(func.sum(RunSession.distance_km), 0))
        .join(Workout, Workout.id == RunSession.workout_id)
        .filter(Workout.user_id == user_id)
        .scalar()
        or 0
    )
    total_swim_distance_km = (
        db.query(func.coalesce(func.sum(SwimSession.distance_m), 0))
        .join(Workout, Workout.id == SwimSession.workout_id)
        .filter(Workout.user_id == user_id)
        .scalar()
        or 0
    )

    return {
        "total_workouts": total_workouts,
        "total_duration_hours": round(total_duration_min / 60, 1),
        "total_distance_km": round(total_run_distance_km + (total_swim_distance_km / 1000), 1),
        "breakdown_by_type": breakdown_by_type,
    }


@router.get("/users/{user_id}/stats/weekly", response_model=list[WeeklyStatsResponse])
def get_weekly_stats(user_id: int, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return weekly workout totals for the last 12 weeks."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} was not found")

    twelve_weeks_ago = datetime.utcnow() - timedelta(weeks=12)
    week_start_expr = func.date_trunc("week", Workout.date)

    rows = (
        db.query(
            week_start_expr.label("week_start"),
            func.count(Workout.id).label("workout_count"),
            func.coalesce(func.sum(Workout.duration_min), 0).label("total_duration_min"),
        )
        .filter(Workout.user_id == user_id, Workout.date >= twelve_weeks_ago)
        .group_by(week_start_expr)
        .order_by(week_start_expr.asc())
        .all()
    )

    return [
        {
            "week_start": row.week_start,
            "workout_count": int(row.workout_count),
            "total_duration_min": int(row.total_duration_min),
        }
        for row in rows
    ]


@router.get("/workouts/overdue", response_model=list[OverdueUserResponse])
def get_overdue_users(days: int = Query(default=7, ge=1), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return users whose last logged workout is older than the provided number of days."""

    now = datetime.now().astimezone()
    cutoff = now - timedelta(days=days)

    users_with_workouts = (
        db.query(User.id, User.username, func.max(Workout.date).label("last_workout_date"))
        .outerjoin(Workout, Workout.user_id == User.id)
        .group_by(User.id, User.username)
        .all()
    )

    results: list[dict[str, Any]] = []
    for user_id, username, last_workout_date in users_with_workouts:
        if last_workout_date is None or last_workout_date < cutoff:
            days_since = None
            if last_workout_date is not None:
                days_since = (now - last_workout_date).days
            results.append(
                {
                    "user_id": user_id,
                    "username": username,
                    "last_workout_date": last_workout_date,
                    "days_since_last_workout": days_since,
                }
            )

    return results
