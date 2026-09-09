from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import (
    Equipment,
    Reservation,
    ReservationStatus,
    User,
    UserRole,
)
from backend.app.security import create_access_token


def add_user_and_headers(
    database_session: Session,
    *,
    email: str,
    role: UserRole = UserRole.USER,
) -> tuple[User, dict[str, str]]:
    user = User(
        email=email,
        full_name="Reservation User",
        password_hash="test-password-hash",
        role=role,
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


def test_admin_reservation_list_requires_authentication(client: TestClient):
    response = client.get("/admin/reservations")

    assert response.status_code == 401


def test_admin_reservation_list_rejects_regular_user(
    client: TestClient,
    database_session: Session,
):
    _user, headers = add_user_and_headers(
        database_session,
        email="member@example.com",
    )

    response = client.get("/admin/reservations", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_admin_can_list_all_reservations_in_time_order(
    client: TestClient,
    database_session: Session,
):
    _admin, admin_headers = add_user_and_headers(
        database_session,
        email="admin@example.com",
        role=UserRole.ADMIN,
    )
    first_user, _first_headers = add_user_and_headers(
        database_session,
        email="first@example.com",
    )
    second_user, _second_headers = add_user_and_headers(
        database_session,
        email="second@example.com",
    )
    equipment = add_equipment(database_session)
    base_time = datetime.now(timezone.utc) + timedelta(days=30)
    later_reservation = add_reservation(
        database_session,
        user=first_user,
        equipment=equipment,
        starts_at=base_time + timedelta(hours=2),
        ends_at=base_time + timedelta(hours=3),
    )
    earlier_reservation = add_reservation(
        database_session,
        user=second_user,
        equipment=equipment,
        starts_at=base_time,
        ends_at=base_time + timedelta(hours=1),
        reservation_status=ReservationStatus.CANCELLED,
    )

    response = client.get("/admin/reservations", headers=admin_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        earlier_reservation.id,
        later_reservation.id,
    ]
    assert {item["user_id"] for item in response.json()} == {
        first_user.id,
        second_user.id,
    }


def test_admin_can_get_any_reservation(
    client: TestClient,
    database_session: Session,
):
    _admin, admin_headers = add_user_and_headers(
        database_session,
        email="admin@example.com",
        role=UserRole.ADMIN,
    )
    user, _user_headers = add_user_and_headers(
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

    response = client.get(
        f"/admin/reservations/{reservation.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == reservation.id
    assert response.json()["user_id"] == user.id


def test_admin_reservation_detail_returns_not_found(
    client: TestClient,
    database_session: Session,
):
    _admin, admin_headers = add_user_and_headers(
        database_session,
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    response = client.get("/admin/reservations/999", headers=admin_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Reservation not found"}


def test_admin_cancellation_rejects_regular_user(
    client: TestClient,
    database_session: Session,
):
    user, user_headers = add_user_and_headers(
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
        f"/admin/reservations/{reservation.id}/cancel",
        headers=user_headers,
    )

    assert response.status_code == 403
    database_session.refresh(reservation)
    assert reservation.status == ReservationStatus.CONFIRMED


def test_admin_can_cancel_another_users_started_reservation(
    client: TestClient,
    database_session: Session,
):
    _admin, admin_headers = add_user_and_headers(
        database_session,
        email="admin@example.com",
        role=UserRole.ADMIN,
    )
    user, _user_headers = add_user_and_headers(
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
        f"/admin/reservations/{reservation.id}/cancel",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == ReservationStatus.CANCELLED.value
    database_session.refresh(reservation)
    assert reservation.status == ReservationStatus.CANCELLED


def test_admin_cancellation_is_idempotent(
    client: TestClient,
    database_session: Session,
):
    _admin, admin_headers = add_user_and_headers(
        database_session,
        email="admin@example.com",
        role=UserRole.ADMIN,
    )
    user, _user_headers = add_user_and_headers(
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
        f"/admin/reservations/{reservation.id}/cancel",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == ReservationStatus.CANCELLED.value
