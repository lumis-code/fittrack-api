from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import UserRegister, Token
from app.services.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)) -> Token:
    """Register a new user and return an access token."""

    duplicate_fields = []
    if db.query(User).filter(User.username == user_data.username).first():
        duplicate_fields.append("username")
    if db.query(User).filter(User.email == user_data.email).first():
        duplicate_fields.append("email")
    if user_data.phone_number is not None and db.query(User).filter(User.phone_number == user_data.phone_number).first():
        duplicate_fields.append("phone_number")
    if user_data.telegram_id is not None and db.query(User).filter(User.telegram_id == user_data.telegram_id).first():
        duplicate_fields.append("telegram_id")

    if duplicate_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Duplicate field(s): {', '.join(duplicate_fields)}")

    user = User(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        telegram_id=user_data.telegram_id,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"user_id": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    """Authenticate with username+password (form) and return an access token."""

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"user_id": user.id})
    return Token(access_token=access_token, token_type="bearer")
