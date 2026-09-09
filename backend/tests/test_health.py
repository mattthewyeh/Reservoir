from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

import backend.app.main as main_module
from backend.app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get(
        "/health",
        headers={"X-Request-ID": "health-check-request"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert response.headers["X-Request-ID"] == "health-check-request"


def test_readiness_check(monkeypatch):
    monkeypatch.setattr(main_module, "check_database_connection", lambda: None)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_check_reports_database_failure(monkeypatch):
    def unavailable_database():
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(
        main_module,
        "check_database_connection",
        unavailable_database,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_invalid_request_id_is_replaced():
    response = client.get("/health", headers={"X-Request-ID": "not valid"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "not valid"
    assert len(response.headers["X-Request-ID"]) == 32
