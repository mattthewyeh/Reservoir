from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import Equipment, User, UserRole
from backend.app.security import create_access_token


def authorization_headers(
    client: TestClient,
    database_session: Session,
    role: UserRole,
) -> dict[str, str]:
    user = User(
        email=f"{role.value}@example.com",
        full_name=f"Example {role.value.title()}",
        password_hash="test-password-hash",
        role=role,
    )
    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)

    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def test_create_equipment_requires_authentication(client: TestClient):
    response = client.post("/equipment", json={"name": "Camera"})

    assert response.status_code == 401


def test_create_equipment_rejects_regular_user(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(client, database_session, UserRole.USER)

    response = client.post("/equipment", json={"name": "Camera"}, headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_admin_can_create_equipment(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(client, database_session, UserRole.ADMIN)

    response = client.post(
        "/equipment",
        json={"name": "  Camera  ", "description": "Mirrorless camera"},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Camera"
    assert response.json()["is_active"] is True
    assert database_session.get(Equipment, response.json()["id"]) is not None


def test_admin_can_update_deactivate_and_reactivate_equipment(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(client, database_session, UserRole.ADMIN)
    equipment = Equipment(name="Camera", description="Old description")
    database_session.add(equipment)
    database_session.commit()
    database_session.refresh(equipment)

    deactivate_response = client.patch(
        f"/equipment/{equipment.id}",
        json={
            "name": "Cinema Camera",
            "description": None,
            "is_active": False,
        },
        headers=headers,
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["name"] == "Cinema Camera"
    assert deactivate_response.json()["description"] is None
    assert deactivate_response.json()["is_active"] is False
    assert client.get(f"/equipment/{equipment.id}").status_code == 404

    reactivate_response = client.patch(
        f"/equipment/{equipment.id}",
        json={"is_active": True},
        headers=headers,
    )

    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["is_active"] is True
    assert client.get(f"/equipment/{equipment.id}").status_code == 200


def test_update_equipment_returns_not_found(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(client, database_session, UserRole.ADMIN)

    response = client.patch(
        "/equipment/999",
        json={"name": "Missing equipment"},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_update_equipment_requires_a_change(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(client, database_session, UserRole.ADMIN)
    equipment = Equipment(name="Camera", description=None)
    database_session.add(equipment)
    database_session.commit()
    database_session.refresh(equipment)

    response = client.patch(
        f"/equipment/{equipment.id}",
        json={},
        headers=headers,
    )

    assert response.status_code == 422
