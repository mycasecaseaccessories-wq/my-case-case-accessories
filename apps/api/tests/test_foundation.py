from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_v1_foundation_endpoint() -> None:
    response = client.get("/api/v1/foundation")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_id_is_generated_and_propagated() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_request_id_is_preserved() -> None:
    response = client.get("/health", headers={"X-Request-ID": "b00-test-request"})
    assert response.headers["X-Request-ID"] == "b00-test-request"
