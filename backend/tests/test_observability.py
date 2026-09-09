import json

from fastapi.testclient import TestClient

from backend.app.observability import access_logger


def test_access_log_is_structured_and_includes_request_id(
    client: TestClient,
    monkeypatch,
):
    messages: list[str] = []
    monkeypatch.setattr(access_logger, "info", messages.append)

    response = client.get(
        "/equipment",
        headers={"X-Request-ID": "equipment-list-request"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "equipment-list-request"
    assert len(messages) == 1

    access_log = json.loads(messages[0])
    assert access_log["event"] == "http_request"
    assert access_log["request_id"] == "equipment-list-request"
    assert access_log["method"] == "GET"
    assert access_log["route"] == "/equipment"
    assert access_log["status"] == 200
    assert access_log["duration_ms"] >= 0
    assert access_log["timestamp"]
