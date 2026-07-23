import asyncio
import os
from datetime import datetime, timezone

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.models.gym_set import GymSet
from app.models.run_session import RunSession
from app.models.swim_session import SwimSession
from app.models.workout import Workout, WorkoutType
from app.services import gemini_client
from app.services.workout_formatter import format_recent_workouts_summary, format_workout_summary


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self._response = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None, timeout=None):
        return self._response


def test_format_workout_summary_for_gym_workout():
    workout = Workout(
        user_id=1,
        type=WorkoutType.GYM,
        date=datetime(2024, 1, 2, 18, 0, tzinfo=timezone.utc),
        duration_min=60,
        notes="Felt strong",
    )
    workout.gym_sets = [
        GymSet(exercise_name="Bench Press", muscle_group="Chest", sets=3, reps=8, weight_kg=70.0)
    ]

    summary = format_workout_summary(workout)

    assert "Workout type: gym" in summary
    assert "Bench Press" in summary
    assert "Felt strong" in summary


def test_format_recent_workouts_summary_returns_separator_joined_text():
    workout_one = Workout(
        user_id=1,
        type=WorkoutType.GYM,
        date=datetime(2024, 1, 2, 18, 0, tzinfo=timezone.utc),
        duration_min=60,
        notes="Felt strong",
    )
    workout_two = Workout(
        user_id=1,
        type=WorkoutType.RUN,
        date=datetime(2024, 1, 3, 19, 0, tzinfo=timezone.utc),
        duration_min=45,
        notes="Easy run",
    )

    summary = format_recent_workouts_summary([workout_one, workout_two])

    assert "Workout type: gym" in summary
    assert "\n---\n" in summary
    assert "Workout type: run" in summary


def test_analyze_workout_extracts_text(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    client = FakeAsyncClient()
    client._response = FakeResponse(payload={"candidates": [{"content": {"parts": [{"text": "Great job"}]}}]})
    monkeypatch.setattr(gemini_client.httpx, "AsyncClient", lambda *args, **kwargs: client)

    result = asyncio.run(gemini_client.analyze_workout("A solid upper-body session"))

    assert result == "Great job"


def test_analyze_workout_raises_clear_error_for_empty_candidates(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    client = FakeAsyncClient()
    client._response = FakeResponse(payload={"candidates": []})
    monkeypatch.setattr(gemini_client.httpx, "AsyncClient", lambda *args, **kwargs: client)

    with pytest.raises(gemini_client.GeminiAPIError, match="no candidates"):
        asyncio.run(gemini_client.analyze_workout("A blocked response"))
