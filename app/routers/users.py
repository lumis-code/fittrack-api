from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
    """Fetch a single user by id. Requires authentication."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )
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
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
    """Partially update a user after validating uniqueness for changed fields."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

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
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    """Delete a user by id."""

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} was not found",
        )
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

    db.delete(user)
    db.commit()
    return None