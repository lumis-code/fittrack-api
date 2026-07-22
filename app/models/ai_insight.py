from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AiInsight(Base):
    """Represents an AI-generated insight for a user or workout."""

    __tablename__ = "ai_insights"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workout_id: Mapped[Optional[int]] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="ai_insights")
    workout: Mapped[Optional["Workout"]] = relationship(back_populates="ai_insights")
