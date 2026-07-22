from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SwimSession(Base):
    """Represents the swimming-specific details of a workout."""

    __tablename__ = "swim_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"), unique=True, nullable=False)
    distance_m: Mapped[int] = mapped_column(nullable=False)
    pool_length_m: Mapped[int] = mapped_column(nullable=False)
    strokes: Mapped[int | None] = mapped_column(nullable=True)
    avg_heart_rate: Mapped[int | None] = mapped_column(nullable=True)

    workout: Mapped["Workout"] = relationship(back_populates="swim_session", uselist=False)
