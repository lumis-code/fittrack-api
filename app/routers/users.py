from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create a new user after validating uniqueness of key fields."""

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate field(s): {', '.join(duplicate_fields)}",
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        telegram_id=user_data.telegram_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/telegram/{telegram_id}", response_model=UserResponse)
def get_user_by_telegram_id(telegram_id: int, db: Session = Depends(get_db)) -> User:
    """Look up a user by their Telegram ID."""

    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    """Fetch a single user by id."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)) -> User:
    """Partially update a user after validating uniqueness for changed fields."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )

    update_data = user_update.model_dump(exclude_unset=True)

    duplicate_fields = []
    if "username" in update_data:
        if db.query(User).filter(User.username == update_data["username"], User.id != user_id).first():
            duplicate_fields.append("username")
    if "email" in update_data:
        if db.query(User).filter(User.email == update_data["email"], User.id != user_id).first():
            duplicate_fields.append("email")
    if "phone_number" in update_data and update_data["phone_number"] is not None:
        if db.query(User).filter(User.phone_number == update_data["phone_number"], User.id != user_id).first():
            duplicate_fields.append("phone_number")
    if "telegram_id" in update_data and update_data["telegram_id"] is not None:
        if db.query(User).filter(User.telegram_id == update_data["telegram_id"], User.id != user_id).first():
            duplicate_fields.append("telegram_id")

    if duplicate_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate field(s): {', '.join(duplicate_fields)}",
        )

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a user by id."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )

    db.delete(user)
    db.commit()
    return None