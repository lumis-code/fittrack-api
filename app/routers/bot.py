from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_bot_service
from app.models import CyclingSession, GymSet, RunSession, SwimSession, User, Workout, WorkoutType
from app.schemas import WorkoutCreate, WorkoutResponse, UserCreate, UserResponse

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/workouts", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def bot_create_workout(workout_data: WorkoutCreate, db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> Workout:
    """Create a workout on behalf of a user (bot-authenticated).

    The `user_id` field in the payload is required and used as the owner.
    """
    # verify the target user exists
    user = db.query(User).filter(User.id == workout_data.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {workout_data.user_id} was not found")

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
        elif workout.type == WorkoutType.CYCLING:
            db.add(
                CyclingSession(
                    workout_id=workout.id,
                    distance_km=workout_data.cycling_session.distance_km,
                    avg_speed_kmh=workout_data.cycling_session.avg_speed_kmh,
                    elevation_m=workout_data.cycling_session.elevation_m,
                    route_name=workout_data.cycling_session.route_name,
                )
            )

        db.commit()
        db.refresh(workout)
    except Exception:
        db.rollback()
        raise

    return (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session), joinedload(Workout.cycling_session))
        .filter(Workout.id == workout.id)
        .first()
    )


@router.get("/workouts", response_model=list[WorkoutResponse])
def bot_list_workouts(user_id: int = Query(...), type: str | None = Query(default=None), date_from: datetime | None = Query(default=None), date_to: datetime | None = Query(default=None), skip: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> list[Workout]:
    """List workouts for a user (bot-authenticated). `user_id` query param is required."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} was not found")

    query = db.query(Workout).options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session), joinedload(Workout.cycling_session))
    query = query.filter(Workout.user_id == user_id)
    if type is not None:
        query = query.filter(Workout.type == WorkoutType(type))
    if date_from is not None:
        query = query.filter(Workout.date >= date_from)
    if date_to is not None:
        query = query.filter(Workout.date <= date_to)

    return query.order_by(Workout.date.desc()).offset(skip).limit(limit).all()


@router.get("/users/telegram/{telegram_id}", response_model=UserResponse)
def bot_get_user_by_telegram_id(telegram_id: int, db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def bot_create_user(user_data: UserCreate, db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> User:
    """Create a user on behalf of the bot (no password)."""
    duplicate_fields = []

    if db.query(User).filter(User.username == user_data.username).first():
        duplicate_fields.append("username")
    if db.query(User).filter(User.email == user_data.email).first():
        duplicate_fields.append("email")
    if user_data.phone_number is not None and db.query(User).filter(User.phone_number == user_data.phone_number).first():
        duplicate_fields.append("phone_number")
    if user_data.telegram_id is not None and db.query(User).filter(User.telegram_id == user_data.telegram_id).first():
        duplicate_fields.append("telegram_id")

    if duplicate_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Duplicate field(s): {', '.join(duplicate_fields)}")

    user = User(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        telegram_id=user_data.telegram_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/ai/analyze/{workout_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bot_analyze_workout(workout_id: int, db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> dict:
    # delegate to existing AI service but ensure caller is the bot; reuse ai logic minimally here
    workout = (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session), joinedload(Workout.cycling_session))
        .filter(Workout.id == workout_id)
        .first()
    )
    if workout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workout with id {workout_id} was not found")
    # Bot is allowed to analyze any workout; the bot provides the user context separately.
    from app.services.gemini_client import analyze_workout, GeminiAPIError
    from app.services.workout_formatter import format_workout_summary

    summary = format_workout_summary(workout)
    try:
        ai_text = await analyze_workout(summary)
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    # store insight
    from app.models import AiInsight

    insight = AiInsight(user_id=workout.user_id, workout_id=workout.id, prompt=summary, response=ai_text)
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return {"id": insight.id, "response": insight.response}


@router.post("/ai/weekly-plan", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bot_weekly_plan(request: dict, db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> dict:
    # minimal wrapper: expect {'user_id': int, 'goal': str|None}
    user_id = request.get("user_id")
    goal = request.get("goal")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} was not found")

    cutoff_date = datetime.utcnow() - timedelta(days=14)
    workouts = (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session), joinedload(Workout.cycling_session))
        .filter(Workout.user_id == user_id)
        .filter(Workout.date >= cutoff_date)
        .order_by(Workout.date.desc())
        .all()
    )
    if not workouts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough workout history to generate a plan")

    from app.services.workout_formatter import format_recent_workouts_summary
    from app.services.gemini_client import generate_weekly_plan, GeminiAPIError

    summary = format_recent_workouts_summary(workouts)
    try:
        ai_text = await generate_weekly_plan(summary, goal)
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    from app.models import AiInsight

    insight = AiInsight(user_id=user_id, workout_id=None, prompt=summary, response=ai_text)
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return {"id": insight.id, "response": insight.response}


@router.get("/users/{user_id}/stats", response_model=dict)
def bot_get_user_stats(user_id: int, db: Session = Depends(get_db), _: None = Depends(get_bot_service)) -> dict[str, Any]:
    """Bot-accessible user stats (same aggregation as /users/{user_id}/stats)."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} was not found")

    workout_counts = (
        db.query(Workout.type, func.count(Workout.id))
        .filter(Workout.user_id == user_id)
        .group_by(Workout.type)
        .all()
    )
    breakdown_by_type = {"gym": 0, "run": 0, "swim": 0, "cycling": 0}
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
    total_cycling_distance_km = (
        db.query(func.coalesce(func.sum(CyclingSession.distance_km), 0))
        .join(Workout, Workout.id == CyclingSession.workout_id)
        .filter(Workout.user_id == user_id)
        .scalar()
        or 0
    )

    return {
        "total_workouts": total_workouts,
        "total_duration_hours": round(total_duration_min / 60, 1),
        "total_distance_km": round(total_run_distance_km + (total_swim_distance_km / 1000) + total_cycling_distance_km, 1),
        "breakdown_by_type": breakdown_by_type,
    }
