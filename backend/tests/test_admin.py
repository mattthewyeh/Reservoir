import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.admin import UserNotFoundError, promote_user_to_admin
from backend.app.models import User, UserRole
from backend.app.security import require_admin


def add_user(
    database_session: Session,
    email: str = "member@example.com",
    role: UserRole = UserRole.USER,
) -> User:
    user = User(
        email=email,
        full_name="Example Member",
        password_hash="test-password-hash",
        role=role,
    )
    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)
    return user


def test_require_admin_allows_admin_user(database_session: Session):
    admin = add_user(database_session, role=UserRole.ADMIN)

    assert require_admin(admin) is admin


def test_require_admin_rejects_regular_user(database_session: Session):
    user = add_user(database_session)

    with pytest.raises(HTTPException) as error:
        require_admin(user)

    assert error.value.status_code == 403
    assert error.value.detail == "Admin access required"


def test_promote_user_to_admin(database_session: Session):
    user = add_user(database_session, email="member@example.com")

    promoted_user = promote_user_to_admin(database_session, "MEMBER@example.com")

    assert promoted_user.id == user.id
    assert promoted_user.role is UserRole.ADMIN


def test_promoting_admin_is_idempotent(database_session: Session):
    admin = add_user(database_session, role=UserRole.ADMIN)

    promoted_user = promote_user_to_admin(database_session, admin.email)

    assert promoted_user.id == admin.id
    assert promoted_user.role is UserRole.ADMIN


def test_promote_user_rejects_unknown_email(database_session: Session):
    with pytest.raises(UserNotFoundError):
        promote_user_to_admin(database_session, "missing@example.com")
