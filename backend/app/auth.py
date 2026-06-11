"""Authentication and role-based access control.

NOTE: password hashing here uses salted SHA-256 for a dependency-light demo.
For production, swap in bcrypt/argon2 (passlib) and move SECRET_KEY into a
managed secret store. The role-gating pattern below is what you'd keep.
"""
import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 240
SALT = "fpna-demo-salt"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

ROLE_RANK = {"viewer": 0, "editor": 1, "admin": 2}


def hash_password(raw: str) -> str:
    return hashlib.sha256((SALT + raw).encode()).hexdigest()


def verify_password(raw: str, hashed: str) -> bool:
    return hash_password(raw) == hashed


def create_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    creds_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise creds_error
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise creds_error
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise creds_error
    return user


def require_role(minimum: str):
    """Dependency factory: blocks users below the required role rank."""
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if ROLE_RANK.get(user.role, -1) < ROLE_RANK[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum}' role or higher",
            )
        return user
    return checker
