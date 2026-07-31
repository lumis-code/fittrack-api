from __future__ import annotations

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CyclingSession(Base):
    """Represents the cycling-specific details of a workout."""

    __tablename__ = "cycling_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"), unique=True, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    avg_speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_m: Mapped[int | None] = mapped_column(nullable=True)
    route_name: Mapped[str | None] = mapped_column(nullable=True)

    workout: Mapped["Workout"] = relationship(back_populates="cycling_session", uselist=False)
