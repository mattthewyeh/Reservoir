from sqlalchemy import CheckConstraint

from backend.app.database import Base
from backend.app.models import Equipment, Reservation, User, UserRole


def test_initial_tables_are_registered():
    assert set(Base.metadata.tables) == {"users", "equipment", "reservations"}


def test_user_role_defaults_to_regular_user():
    role_column = User.__table__.c.role

    assert role_column.default.arg is UserRole.USER
    assert role_column.server_default.arg == UserRole.USER.value


def test_reservation_relates_user_and_equipment():
    assert Reservation.user.property.mapper.class_ is User
    assert Reservation.equipment.property.mapper.class_ is Equipment


def test_reservation_requires_end_after_start():
    check_constraints = {
        constraint.name
        for constraint in Reservation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "end_after_start" in check_constraints
