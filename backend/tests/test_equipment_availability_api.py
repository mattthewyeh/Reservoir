from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import Equipment, Reservation, ReservationStatus, User


AVAILABILITY_RANGE = {
    "starts_at": "2030-01-15T17:00:00Z",
    "ends_at": "2030-01-15T19:00:00Z",
}


def add_equipment(
    database_session: Session,
    name: str,
    *,
    is_active: bool = True,
) -> Equipment:
    equipment = Equipment(
        name=name,
        description=f"{name} description",
        is_active=is_active,
    )
    database_session.add(equipment)
    database_session.commit()
    database_session.refresh(equipment)
    return equipment


def add_user(database_session: Session) -> User:
    user = User(
        email="member@example.com",
        full_name="Example Member",
        password_hash="test-password-hash",
    )
    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)
    return user


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


def test_availability_returns_active_equipment_in_name_order_without_authentication(
    client: TestClient,
    database_session: Session,
):
    add_equipment(database_session, "Tripod")
    add_equipment(database_session, "Camera")
    add_equipment(database_session, "Retired microphone", is_active=False)

    response = client.get("/equipment/availability", params=AVAILABILITY_RANGE)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Camera", "Tripod"]


def test_availability_excludes_equipment_with_confirmed_overlap(
    client: TestClient,
    database_session: Session,
):
    user = add_user(database_session)
    reserved_equipment = add_equipment(database_session, "Camera")
    available_equipment = add_equipment(database_session, "Tripod")
    add_reservation(
        database_session,
        user=user,
        equipment=reserved_equipment,
        starts_at=datetime(2030, 1, 15, 18, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 20, tzinfo=timezone.utc),
    )

    response = client.get("/equipment/availability", params=AVAILABILITY_RANGE)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [available_equipment.id]


def test_availability_normalizes_query_offsets_to_utc(
    client: TestClient,
    database_session: Session,
):
    user = add_user(database_session)
    equipment = add_equipment(database_session, "Camera")
    add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=datetime(2030, 1, 15, 17, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 19, tzinfo=timezone.utc),
    )

    response = client.get(
        "/equipment/availability",
        params={
            "starts_at": "2030-01-15T09:00:00-08:00",
            "ends_at": "2030-01-15T11:00:00-08:00",
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_availability_allows_boundaries_and_ignores_cancelled_reservations(
    client: TestClient,
    database_session: Session,
):
    user = add_user(database_session)
    adjacent_equipment = add_equipment(database_session, "Camera")
    cancelled_equipment = add_equipment(database_session, "Tripod")
    add_reservation(
        database_session,
        user=user,
        equipment=adjacent_equipment,
        starts_at=datetime(2030, 1, 15, 15, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 17, tzinfo=timezone.utc),
    )
    add_reservation(
        database_session,
        user=user,
        equipment=cancelled_equipment,
        starts_at=datetime(2030, 1, 15, 18, tzinfo=timezone.utc),
        ends_at=datetime(2030, 1, 15, 20, tzinfo=timezone.utc),
        reservation_status=ReservationStatus.CANCELLED,
    )

    response = client.get("/equipment/availability", params=AVAILABILITY_RANGE)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        adjacent_equipment.id,
        cancelled_equipment.id,
    ]


@pytest.mark.parametrize(
    ("starts_at", "ends_at"),
    [
        ("2030-01-15T17:00:00", "2030-01-15T19:00:00"),
        ("2030-01-15T19:00:00Z", "2030-01-15T17:00:00Z"),
        ("2030-01-15T17:00:00Z", "2030-01-15T17:00:00Z"),
    ],
)
def test_availability_rejects_invalid_time_ranges(
    client: TestClient,
    starts_at: str,
    ends_at: str,
):
    response = client.get(
        "/equipment/availability",
        params={"starts_at": starts_at, "ends_at": ends_at},
    )

    assert response.status_code == 422
