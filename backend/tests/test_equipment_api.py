from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import Equipment


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session

    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def client(database_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield database_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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


def test_list_equipment_returns_active_items_in_name_order(
    client: TestClient,
    database_session: Session,
):
    add_equipment(database_session, "Tripod")
    add_equipment(database_session, "Camera")
    add_equipment(database_session, "Retired microphone", is_active=False)

    response = client.get("/equipment")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Camera", "Tripod"]


def test_get_equipment_returns_active_item(
    client: TestClient,
    database_session: Session,
):
    equipment = add_equipment(database_session, "Camera")

    response = client.get(f"/equipment/{equipment.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": equipment.id,
        "name": "Camera",
        "description": "Camera description",
        "is_active": True,
        "created_at": equipment.created_at.isoformat(),
    }


def test_get_equipment_returns_not_found_for_missing_item(client: TestClient):
    response = client.get("/equipment/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}


def test_get_equipment_hides_inactive_item(
    client: TestClient,
    database_session: Session,
):
    equipment = add_equipment(database_session, "Retired microphone", is_active=False)

    response = client.get(f"/equipment/{equipment.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Equipment not found"}
