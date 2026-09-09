from fastapi.testclient import TestClient


def test_metrics_endpoint_exposes_prometheus_metrics(client: TestClient):
    client.get("/health")

    response = client.get("/metrics/")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "reservoir_http_requests_total" in response.text
    assert 'method="GET",route="/health",status="200"' in response.text


def test_metrics_use_stable_label_for_unmatched_routes(client: TestClient):
    client.get("/a-path-that-does-not-exist")

    response = client.get("/metrics/")

    assert 'route="unmatched",status="404"' in response.text
    assert "/a-path-that-does-not-exist" not in response.text
