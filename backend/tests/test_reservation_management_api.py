from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import Equipment, Reservation, ReservationStatus, User
from backend.app.security import create_access_token


def add_user_and_headers(
    database_session: Session,
    *,
    email: str,
) -> tuple[User, dict[str, str]]:
    user = User(
        email=email,
        full_name="Reservation Member",
        password_hash="test-password-hash",
    )
    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)
    return user, {"Authorization": f"Bearer {create_access_token(user.id)}"}


def add_equipment(database_session: Session) -> Equipment:
    equipment = Equipment(name="Camera", description="Mirrorless camera")
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


def test_list_reservations_requires_authentication(client: TestClient):
    response = client.get("/reservations")

    assert response.status_code == 401


def test_list_reservations_returns_only_current_users_reservations_in_time_order(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    other_user, _other_headers = add_user_and_headers(
        database_session,
        email="other@example.com",
    )
    equipment = add_equipment(database_session)
    base_time = datetime.now(timezone.utc) + timedelta(days=30)

    later_reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=base_time + timedelta(hours=4),
        ends_at=base_time + timedelta(hours=5),
    )
    earlier_reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=base_time,
        ends_at=base_time + timedelta(hours=1),
        reservation_status=ReservationStatus.CANCELLED,
    )
    add_reservation(
        database_session,
        user=other_user,
        equipment=equipment,
        starts_at=base_time + timedelta(hours=2),
        ends_at=base_time + timedelta(hours=3),
    )

    response = client.get("/reservations", headers=headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        earlier_reservation.id,
        later_reservation.id,
    ]
    assert {item["user_id"] for item in response.json()} == {user.id}


def test_user_can_get_own_reservation(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
    )

    response = client.get(f"/reservations/{reservation.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == reservation.id
    assert response.json()["user_id"] == user.id


def test_get_reservation_hides_other_users_reservation(
    client: TestClient,
    database_session: Session,
):
    _user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    other_user, _other_headers = add_user_and_headers(
        database_session,
        email="other@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=other_user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
    )

    response = client.get(f"/reservations/{reservation.id}", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Reservation not found"}


def test_cancel_reservation_requires_authentication(
    client: TestClient,
    database_session: Session,
):
    user, _headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
    )

    response = client.post(f"/reservations/{reservation.id}/cancel")

    assert response.status_code == 401


def test_user_can_cancel_own_future_reservation(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
    )

    response = client.post(
        f"/reservations/{reservation.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == ReservationStatus.CANCELLED.value
    database_session.refresh(reservation)
    assert reservation.status == ReservationStatus.CANCELLED


def test_cancel_reservation_hides_other_users_reservation(
    client: TestClient,
    database_session: Session,
):
    _user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    other_user, _other_headers = add_user_and_headers(
        database_session,
        email="other@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=other_user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
    )

    response = client.post(
        f"/reservations/{reservation.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Reservation not found"}
    database_session.refresh(reservation)
    assert reservation.status == ReservationStatus.CONFIRMED


def test_started_reservation_cannot_be_cancelled(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    equipment = add_equipment(database_session)
    current_time = datetime.now(timezone.utc)
    reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=current_time - timedelta(hours=1),
        ends_at=current_time + timedelta(hours=1),
    )

    response = client.post(
        f"/reservations/{reservation.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Reservation can no longer be cancelled"}
    database_session.refresh(reservation)
    assert reservation.status == ReservationStatus.CONFIRMED


def test_cancelling_reservation_twice_is_idempotent(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
        reservation_status=ReservationStatus.CANCELLED,
    )

    response = client.post(
        f"/reservations/{reservation.id}/cancel",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == ReservationStatus.CANCELLED.value


def test_cancelling_reservation_releases_time_for_new_booking(
    client: TestClient,
    database_session: Session,
):
    user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )
    equipment = add_equipment(database_session)
    start_time = datetime.now(timezone.utc) + timedelta(days=30)
    reservation = add_reservation(
        database_session,
        user=user,
        equipment=equipment,
        starts_at=start_time,
        ends_at=start_time + timedelta(hours=1),
    )

    cancel_response = client.post(
        f"/reservations/{reservation.id}/cancel",
        headers=headers,
    )
    create_response = client.post(
        "/reservations",
        json={
            "equipment_id": equipment.id,
            "starts_at": start_time.isoformat(),
            "ends_at": (start_time + timedelta(hours=1)).isoformat(),
        },
        headers=headers,
    )

    assert cancel_response.status_code == 200
    assert create_response.status_code == 201
    assert create_response.json()["id"] != reservation.id
