from datetime import datetime, timezone

from app.models.cycling_session import CyclingSession
from app.models.workout import Workout, WorkoutType
from app.services.workout_formatter import format_workout_summary


def test_format_workout_summary_for_cycling_workout():
    workout = Workout(
        user_id=1,
        type=WorkoutType.CYCLING,
        date=datetime(2024, 1, 2, 18, 0, tzinfo=timezone.utc),
        duration_min=60,
        notes="Great ride",
    )
    workout.cycling_session = CyclingSession(
        distance_km=25.5,
        avg_speed_kmh=24.0,
        elevation_m=300,
        route_name="River loop",
    )

    summary = format_workout_summary(workout)

    assert "Workout type: cycling" in summary
    assert "25.5" in summary
    assert "River loop" in summary
