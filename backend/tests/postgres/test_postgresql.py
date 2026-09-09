from datetime import datetime, timezone
from pathlib import Path
from subprocess import CompletedProcess
from typing import Protocol

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import (
    RESERVATION_OVERLAP_CONSTRAINT,
    Equipment,
    Reservation,
    ReservationStatus,
    User,
)


pytestmark = pytest.mark.postgres
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class AlembicRunner(Protocol):
    def __call__(self, *arguments: str) -> CompletedProcess[str]: ...


def current_migration_head() -> str:
    configuration = Config(PROJECT_ROOT / "alembic.ini")
    return ScriptDirectory.from_config(configuration).get_current_head()


def test_migrations_upgrade_from_empty_database_and_are_reversible(
    postgres_database_url: str,
    run_alembic: AlembicRunner,
):
    run_alembic("upgrade", "head")
    engine = create_engine(postgres_database_url)

    with engine.connect() as connection:
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version",
            "equipment",
            "reservations",
            "users",
        }
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            current_migration_head()
        )
        assert connection.scalar(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conname = :constraint_name
                      AND contype = 'x'
                )
                """
            ),
            {"constraint_name": RESERVATION_OVERLAP_CONSTRAINT},
        )
        assert connection.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'btree_gist')")
        )

    engine.dispose()
    run_alembic("downgrade", "base")
    engine = create_engine(postgres_database_url)

    with engine.connect() as connection:
        assert inspect(connection).get_table_names() == ["alembic_version"]
        assert connection.scalar(text("SELECT count(*) FROM alembic_version")) == 0
        assert connection.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'btree_gist')")
        )

    engine.dispose()
    run_alembic("upgrade", "head")
    engine = create_engine(postgres_database_url)

    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            current_migration_head()
        )

    engine.dispose()
    run_alembic("check")


def test_postgresql_rejects_overlapping_confirmed_reservations(
    postgres_database_url: str,
    run_alembic: AlembicRunner,
):
    run_alembic("upgrade", "head")
    engine = create_engine(postgres_database_url)

    with Session(engine, expire_on_commit=False) as session:
        user = User(
            email="member@example.com",
            full_name="Example Member",
            password_hash="test-password-hash",
        )
        equipment = Equipment(name="Camera", description="Mirrorless camera")
        session.add_all([user, equipment])
        session.commit()

        session.add(
            Reservation(
                user_id=user.id,
                equipment_id=equipment.id,
                starts_at=datetime(2030, 1, 15, 17, tzinfo=timezone.utc),
                ends_at=datetime(2030, 1, 15, 19, tzinfo=timezone.utc),
            )
        )
        session.commit()

        session.add(
            Reservation(
                user_id=user.id,
                equipment_id=equipment.id,
                starts_at=datetime(2030, 1, 15, 18, tzinfo=timezone.utc),
                ends_at=datetime(2030, 1, 15, 20, tzinfo=timezone.utc),
            )
        )

        with pytest.raises(IntegrityError) as error:
            session.commit()

        assert error.value.orig.diag.constraint_name == RESERVATION_OVERLAP_CONSTRAINT
        session.rollback()

        session.add_all(
            [
                Reservation(
                    user_id=user.id,
                    equipment_id=equipment.id,
                    starts_at=datetime(2030, 1, 15, 19, tzinfo=timezone.utc),
                    ends_at=datetime(2030, 1, 15, 20, tzinfo=timezone.utc),
                ),
                Reservation(
                    user_id=user.id,
                    equipment_id=equipment.id,
                    starts_at=datetime(2030, 1, 15, 18, tzinfo=timezone.utc),
                    ends_at=datetime(2030, 1, 15, 18, 30, tzinfo=timezone.utc),
                    status=ReservationStatus.CANCELLED,
                ),
            ]
        )
        session.commit()

    engine.dispose()
