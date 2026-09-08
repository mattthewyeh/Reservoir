from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.schemas import Token, UserCreate, UserRead
from backend.app.security import (
    CurrentUser,
    authenticate_user,
    create_access_token,
    hash_password,
)


router = APIRouter(prefix="/auth", tags=["authentication"])
DatabaseSession = Annotated[Session, Depends(get_db)]
LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, database: DatabaseSession):
    normalized_email = str(user_data.email).lower()
    existing_user = database.scalar(select(User).where(User.email == normalized_email))

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=normalized_email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password.get_secret_value()),
    )
    database.add(user)

    try:
        database.commit()
    except IntegrityError:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None

    database.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login_for_access_token(form_data: LoginForm, database: DatabaseSession):
    user = authenticate_user(database, form_data.username, form_data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser):
    return current_user
