"""
Security helpers: password hashing, JWT token creation/verification,
and the dependency chain used to protect routes.
"""

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app import models

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Turn a plain password into a one-way bcrypt hash."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain password against a stored bcrypt hash, without reversing it."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """Build and sign a JWT that proves who the logged-in user is."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    """Verify a JWT's signature and return its contents, or None if it's invalid or expired."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        return None


# ---------------------------------------------------------------------------
# Dependency chain, three layers deep:
#   Layer 1: get_db                 -> opens a database session
#   Layer 2: get_current_user       -> depends on get_db + the bearer token
#   Layer 3: get_current_instructor -> depends on get_current_user
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Layer 2 dependency. Reads the JWT from the Authorization header,
    verifies it, and returns the matching logged-in user. Used directly
    by several routers (users, courses, orders) - this is the dependency
    reused across more than one API.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_instructor(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Layer 3 dependency. Builds on top of get_current_user and additionally
    requires the logged-in user to be an instructor. Used by the "create
    course" route, giving that one route a 3-layer dependency chain:
    get_db -> get_current_user -> get_current_instructor.
    """
    if not current_user.is_instructor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors are allowed to do this",
        )
    return current_user
