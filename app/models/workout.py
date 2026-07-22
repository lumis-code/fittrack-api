from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkoutType(str, Enum):
    """Supported workout sport types."""

    GYM = "gym"
    RUN = "run"
    SWIM = "swim"


class Workout(Base):
    """Represents a single workout entry for a user."""

    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[WorkoutType] = mapped_column(SQLAlchemyEnum(WorkoutType, name="workout_type"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min: Mapped[int] = mapped_column(nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="workouts")
    gym_sets: Mapped[list["GymSet"]] = relationship(back_populates="workout", cascade="all, delete-orphan")
    run_session: Mapped[Optional["RunSession"]] = relationship(back_populates="workout", uselist=False, cascade="all, delete-orphan")
    swim_session: Mapped[Optional["SwimSession"]] = relationship(back_populates="workout", uselist=False, cascade="all, delete-orphan")
    ai_insights: Mapped[list["AiInsight"]] = relationship(back_populates="workout", cascade="all, delete-orphan")
