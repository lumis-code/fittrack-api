from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import AiInsight, User, Workout
from app.schemas import AiInsightResponse
from app.services.gemini_client import GeminiAPIError, analyze_workout, generate_weekly_plan
from app.services.workout_formatter import format_recent_workouts_summary, format_workout_summary

router = APIRouter(prefix="/ai", tags=["ai"])


class WeeklyPlanRequest(BaseModel):
    user_id: int
    goal: str | None = None


@router.post("/analyze/{workout_id}", response_model=AiInsightResponse, status_code=status.HTTP_201_CREATED)
async def analyze_workout_endpoint(workout_id: int, db: Session = Depends(get_db)) -> AiInsight:
    workout = (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session))
        .filter(Workout.id == workout_id)
        .first()
    )
    if workout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workout with id {workout_id} was not found")

    summary = format_workout_summary(workout)
    try:
        ai_text = await analyze_workout(summary)
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    insight = AiInsight(user_id=workout.user_id, workout_id=workout.id, prompt=summary, response=ai_text)
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.post("/weekly-plan", response_model=AiInsightResponse, status_code=status.HTTP_201_CREATED)
async def generate_weekly_plan_endpoint(request: WeeklyPlanRequest, db: Session = Depends(get_db)) -> AiInsight:
    user = db.query(User).filter(User.id == request.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {request.user_id} was not found")

    cutoff_date = datetime.utcnow() - timedelta(days=14)
    workouts = (
        db.query(Workout)
        .options(joinedload(Workout.gym_sets), joinedload(Workout.run_session), joinedload(Workout.swim_session))
        .filter(Workout.user_id == request.user_id)
        .filter(Workout.date >= cutoff_date)
        .order_by(Workout.date.desc())
        .all()
    )
    if not workouts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough workout history to generate a plan")

    summary = format_recent_workouts_summary(workouts)
    try:
        ai_text = await generate_weekly_plan(summary, request.goal)
    except GeminiAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    insight = AiInsight(user_id=request.user_id, workout_id=None, prompt=summary, response=ai_text)
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/insights/{user_id}", response_model=list[AiInsightResponse])
def list_insights(user_id: int, db: Session = Depends(get_db)) -> list[AiInsight]:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} was not found")

    return (
        db.query(AiInsight)
        .filter(AiInsight.user_id == user_id)
        .order_by(AiInsight.created_at.desc())
        .all()
    )
