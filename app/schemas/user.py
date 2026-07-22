from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Shared user fields."""

    username: str = Field(..., description="Unique display name for the user")
    email: EmailStr = Field(..., description="Unique email address")
    phone_number: Optional[str] = Field(default=None, description="Optional phone number")
    telegram_id: Optional[int] = Field(default=None, description="Optional Telegram user id")


class UserCreate(UserBase):
    """Fields accepted when creating a user."""


class UserUpdate(BaseModel):
    """Fields accepted for partial updates."""

    model_config = ConfigDict(extra="forbid")

    username: Optional[str] = Field(default=None, description="Updated display name")
    email: Optional[EmailStr] = Field(default=None, description="Updated email address")
    phone_number: Optional[str] = Field(default=None, description="Optional phone number")
    telegram_id: Optional[int] = Field(default=None, description="Optional Telegram user id")


class UserResponse(UserBase):
    """User representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
