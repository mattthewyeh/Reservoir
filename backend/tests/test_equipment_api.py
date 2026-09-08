from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models import Equipment


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
