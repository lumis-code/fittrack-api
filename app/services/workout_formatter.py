from __future__ import annotations

from app.models.gym_set import GymSet
from app.models.run_session import RunSession
from app.models.swim_session import SwimSession
from app.models.workout import Workout, WorkoutType


def format_workout_summary(workout: Workout) -> str:
    """Convert a workout ORM object into a human-readable AI summary string."""

    lines = [
        f"Workout type: {workout.type.value}",
        f"Date: {workout.date.strftime('%Y-%m-%d %H:%M')}",
        f"Duration: {workout.duration_min} minutes",
    ]

    if workout.notes:
        lines.append(f"Notes: {workout.notes}")

    if workout.type == WorkoutType.GYM:
        lines.append("Gym details:")
        gym_sets = workout.gym_sets or []
        if gym_sets:
            for set_entry in gym_sets:
                lines.append(
                    f"- {set_entry.exercise_name} ({set_entry.muscle_group}): {set_entry.sets} sets x {set_entry.reps} reps @ {set_entry.weight_kg} kg"
                )
        else:
            lines.append("- No gym exercises recorded")
    elif workout.type == WorkoutType.RUN:
        run_session = workout.run_session
        lines.append("Run details:")
        if run_session:
            lines.append(f"- Distance: {run_session.distance_km} km")
            lines.append(f"- Avg pace: {run_session.avg_pace_min_km} min/km")
            if run_session.elevation_m is not None:
                lines.append(f"- Elevation: {run_session.elevation_m} m")
            if run_session.route_name:
                lines.append(f"- Route: {run_session.route_name}")
        else:
            lines.append("- No run session details recorded")
    elif workout.type == WorkoutType.SWIM:
        swim_session = workout.swim_session
        lines.append("Swim details:")
        if swim_session:
            lines.append(f"- Distance: {swim_session.distance_m} m")
            lines.append(f"- Pool length: {swim_session.pool_length_m} m")
            if swim_session.strokes is not None:
                lines.append(f"- Strokes: {swim_session.strokes}")
            if swim_session.avg_heart_rate is not None:
                lines.append(f"- Avg heart rate: {swim_session.avg_heart_rate}")
        else:
            lines.append("- No swim session details recorded")

    return "\n".join(lines)


def format_recent_workouts_summary(workouts: list[Workout]) -> str:
    """Join multiple workout summaries into a single prompt-friendly text block."""

    if not workouts:
        return "No recent workouts recorded."

    summaries = [format_workout_summary(workout) for workout in workouts]
    return "\n---\n".join(summaries)
