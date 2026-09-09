from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import Equipment, User, UserRole
from backend.app.security import create_access_token


def authorization_headers(
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


def test_frontend_origin_is_allowed_by_cors(client: TestClient):
    response = client.options(
        "/equipment",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )


def test_admin_equipment_list_rejects_regular_user(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(database_session, UserRole.USER)

    response = client.get("/admin/equipment", headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}


def test_admin_equipment_list_includes_inactive_items(
    client: TestClient,
    database_session: Session,
):
    headers = authorization_headers(database_session, UserRole.ADMIN)
    database_session.add_all(
        [
            Equipment(name="Tripod", description=None, is_active=True),
            Equipment(name="Archived camera", description=None, is_active=False),
        ]
    )
    database_session.commit()

    response = client.get("/admin/equipment", headers=headers)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == [
        "Archived camera",
        "Tripod",
    ]
    assert [item["is_active"] for item in response.json()] == [False, True]
