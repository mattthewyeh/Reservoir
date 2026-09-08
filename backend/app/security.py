import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User


load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hasher = PasswordHash.recommended()
dummy_password_hash = password_hasher.hash("not-a-real-user-password")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerToken = Annotated[str, Depends(oauth2_scheme)]


def get_jwt_secret() -> str:
    jwt_secret = os.getenv("JWT_SECRET")

    if not jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured")

    return jwt_secret


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def authenticate_user(database: Session, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    user = database.scalar(select(User).where(User.email == normalized_email))

    if user is None:
        verify_password(password, dummy_password_hash)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": f"user:{user_id}",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, get_jwt_secret(), algorithm=ALGORITHM)


def invalid_credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: BearerToken, database: DatabaseSession) -> User:
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[ALGORITHM])
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.startswith("user:"):
            raise invalid_credentials_exception()

        user_id = int(subject.removeprefix("user:"))
    except (InvalidTokenError, ValueError):
        raise invalid_credentials_exception() from None

    user = database.get(User, user_id)

    if user is None:
        raise invalid_credentials_exception()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
