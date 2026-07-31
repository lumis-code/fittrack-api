from __future__ import annotations

from passlib.context import CryptContext
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
from jose import jwt, JWTError

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY: str = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env — required for JWT signing")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 60)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Returns the hashed password string suitable for storage in the DB.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token containing the provided data.

    The token will include the `sub` claim and an expiration time.
    """
    to_encode = data.copy()
    if expires_delta is None:
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires = datetime.utcnow() + expires_delta

    # Ensure subject exists (prefer explicit 'sub' or fallback to 'user_id')
    sub_value = to_encode.get("sub") or to_encode.get("user_id")
    if not sub_value:
        raise ValueError("create_access_token requires 'sub' or 'user_id' in data")
    sub = str(sub_value)
    to_encode.update({"exp": expires, "sub": sub})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Returns the token payload as a dict, or raises ValueError on failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise ValueError("Token is invalid or expired") from exc
