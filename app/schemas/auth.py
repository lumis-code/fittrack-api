from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(..., description="Unique display name for the user")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Plaintext password")
    phone_number: Optional[str] = Field(default=None, description="Optional phone number")
    telegram_id: Optional[int] = Field(default=None, description="Optional Telegram user id")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
