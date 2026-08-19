from fastapi.testclient import TestClient

from backend.app import app


def test_settings_route_available():
    client = TestClient(app)
    response = client.get("/api/settings")
    assert response.status_code == 200


def test_openapi_contains_existing_routes():
    client = TestClient(app)
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/games" in paths
    assert "/api/profile" in paths
    assert "/api/play/bot/games" in paths
