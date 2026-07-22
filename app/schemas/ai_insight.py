from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AiInsightBase(BaseModel):
    """Shared AI insight fields."""

    prompt: str = Field(..., description="Prompt sent to the AI assistant")
    response: str = Field(..., description="AI-generated response")


class AiInsightResponse(AiInsightBase):
    """AI insight representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    workout_id: int | None = None
    created_at: datetime
