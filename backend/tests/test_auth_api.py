from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import User, UserRole
from backend.app.security import verify_password


REGISTERED_USER = {
    "email": "member@example.com",
    "full_name": "Example Member",
    "password": "correct-horse-battery-staple",
}


def register_user(client: TestClient) -> dict:
    response = client.post("/auth/register", json=REGISTERED_USER)
    assert response.status_code == 201
    return response.json()


def test_register_user_hashes_password_and_returns_safe_profile(
    client: TestClient,
    database_session: Session,
):
    profile = register_user(client)
    stored_user = database_session.scalar(
        select(User).where(User.email == REGISTERED_USER["email"])
    )

    assert profile["email"] == REGISTERED_USER["email"]
    assert profile["role"] == UserRole.USER.value
    assert "password" not in profile
    assert stored_user is not None
    assert stored_user.password_hash != REGISTERED_USER["password"]
    assert verify_password(REGISTERED_USER["password"], stored_user.password_hash)


def test_register_user_rejects_duplicate_email(client: TestClient):
    register_user(client)

    response = client.post("/auth/register", json=REGISTERED_USER)

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_login_and_read_current_user(client: TestClient):
    registered_profile = register_user(client)

    login_response = client.post(
        "/auth/token",
        data={
            "username": REGISTERED_USER["email"],
            "password": REGISTERED_USER["password"],
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    profile_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert profile_response.status_code == 200
    assert profile_response.json() == registered_profile


def test_login_rejects_incorrect_password(client: TestClient):
    register_user(client)

    response = client.post(
        "/auth/token",
        data={
            "username": REGISTERED_USER["email"],
            "password": "incorrect-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_current_user_rejects_invalid_token(client: TestClient):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
