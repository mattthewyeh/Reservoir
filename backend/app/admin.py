from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import User, UserRole


class UserNotFoundError(Exception):
    pass


def promote_user_to_admin(database: Session, email: str) -> User:
    normalized_email = email.strip().lower()
    user = database.scalar(select(User).where(User.email == normalized_email))

    if user is None:
        raise UserNotFoundError(normalized_email)

    if user.role is not UserRole.ADMIN:
        user.role = UserRole.ADMIN
        database.commit()
        database.refresh(user)

    return user
