from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import (
    RESERVATION_OVERLAP_CONSTRAINT,
    Equipment,
    Reservation,
    ReservationStatus,
    User,
    UserRole,
)
from backend.app.security import create_access_token


RESERVATION_TIMES = {
    "starts_at": "2030-01-15T09:00:00-08:00",
    "ends_at": "2030-01-15T11:00:00-08:00",
}


def parse_api_timestamp(timestamp: str) -> datetime:
    parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    if parsed_timestamp.tzinfo is None:
        parsed_timestamp = parsed_timestamp.replace(tzinfo=timezone.utc)

    return parsed_timestamp.astimezone(timezone.utc)


def add_user_and_headers(
    client: TestClient,
    database_session: Session,
) -> tuple[User, dict[str, str]]:
    user = User(
        email="member@example.com",
        full_name="Example Member",
        password_hash="test-password-hash",
        role=UserRole.USER,
    )
    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)

    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    return user, headers


def add_equipment(database_session: Session, *, is_active: bool = True) -> Equipment:
    equipment = Equipment(
        name="Camera",
        description="Mirrorless camera",
        is_active=is_active,
    )
    database_session.add(equipment)
    database_session.commit()
    database_session.refresh(equipment)
    return equipment


def add_reservation(
    database_session: Session,
    *,
    user: User,
    equipment: Equipment,
    starts_at: datetime,
    ends_at: datetime,
    reservation_status: ReservationStatus = ReservationStatus.CONFIRMED,
) -> Reservation:
    reservation = Reservation(
        user_id=user.id,
        equipment_id=equipment.id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=reservation_status,
    )
    database_session.add(reservation)
    database_session.commit()
    database_session.refresh(reservation)
    return reservation


def test_create_reservation_requires_authentication(
    client: TestClient,
    database_session: Session,
):
    equipment = add_equipment(database_session)

    response = client.post(
        "/reservations",
        json={"equipment_id": equipment.id, **RESERVATION_TIMES},
    )

    assert response.status_code == 401


def test_user_can_create_reservation_for_active_equipment(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)

    response = client.post(
        "/reservations",
        json={"equipment_id": equipment.id, **RESERVATION_TIMES},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == user.id
    assert response.json()["equipment_id"] == equipment.id
    assert response.json()["status"] == ReservationStatus.CONFIRMED.value
    assert parse_api_timestamp(response.json()["starts_at"]) == datetime(
        2030, 1, 15, 17, tzinfo=timezone.utc
    )
    assert parse_api_timestamp(response.json()["ends_at"]) == datetime(
        2030, 1, 15, 19, tzinfo=timezone.utc
    )
    assert database_session.get(Reservation, response.json()["id"]) is not None


def test_create_reservation_hides_inactive_equipment(
    client: TestClient,
    database_session: Session,
):
    _user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session, is_active=False)

    response = client.post(
        "/reservations",
        json={"equipment_id": equipment.id, **RESERVATION_TIMES},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_create_reservation_requires_timezone_aware_times(
    client: TestClient,
    database_session: Session,
):
    _user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)

    response = client.post(
        "/reservations",
        json={
            "equipment_id": equipment.id,
            "starts_at": "2030-01-15T09:00:00",
            "ends_at": "2030-01-15T11:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_reservation_requires_end_after_start(
    client: TestClient,
    database_session: Session,
):
    _user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)

    response = client.post(
        "/reservations",
        json={
            "equipment_id": equipment.id,
            "starts_at": "2030-01-15T11:00:00Z",
            "ends_at": "2030-01-15T09:00:00Z",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_reservation_rejects_client_supplied_user_id(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)

    response = client.post(
        "/reservations",
        json={
            "equipment_id": equipment.id,
            "user_id": user.id + 1,
            **RESERVATION_TIMES,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_reservation_rejects_overlapping_confirmed_reservation(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)
    add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=datetime(2030, 1, 15, 17, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 19, tzinfo=timezone.utc),
    )

    response = client.post(
        "/reservations",
        json={
            "equipment_id": equipment.id,
            "starts_at": "2030-01-15T18:00:00Z",
            "ends_at": "2030-01-15T20:00:00Z",
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Equipment is already reserved for this time"
    }
    assert database_session.query(Reservation).count() == 1


def test_create_reservation_allows_back_to_back_reservations(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)
    add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=datetime(2030, 1, 15, 17, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 19, tzinfo=timezone.utc),
    )

    response = client.post(
        "/reservations",
        json={
            "equipment_id": equipment.id,
            "starts_at": "2030-01-15T19:00:00Z",
            "ends_at": "2030-01-15T20:00:00Z",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert database_session.query(Reservation).count() == 2


def test_cancelled_reservation_does_not_block_new_reservation(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)
    add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=datetime(2030, 1, 15, 17, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 19, tzinfo=timezone.utc),
        reservation_status=ReservationStatus.CANCELLED,
    )

    response = client.post(
        "/reservations",
        json={"equipment_id": equipment.id, **RESERVATION_TIMES},
        headers=headers,
    )

    assert response.status_code == 201
    assert database_session.query(Reservation).count() == 2


def test_database_overlap_violation_becomes_conflict_response(
    client: TestClient,
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    _user, headers = add_user_and_headers(client, database_session)
    equipment = add_equipment(database_session)

    class ConstraintDiagnostics:
        constraint_name = RESERVATION_OVERLAP_CONSTRAINT

    class ConcurrentOverlapError(Exception):
        diag = ConstraintDiagnostics()

    def reject_concurrent_overlap() -> None:
        raise IntegrityError(
            "INSERT INTO reservations",
            {},
            ConcurrentOverlapError(),
        )

    monkeypatch.setattr(database_session, "commit", reject_concurrent_overlap)

    response = client.post(
        "/reservations",
        json={"equipment_id": equipment.id, **RESERVATION_TIMES},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Equipment is already reserved for this time"
    }
    assert database_session.query(Reservation).count() == 0
