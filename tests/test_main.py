from fastapi.testclient import TestClient

from template_sample_app.main import app

client = TestClient(app)


def test_health_reports_status_and_utc_timestamp() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"] == app.version
    assert body["timestamp_utc"].endswith("+00:00")


def test_root() -> None:
    assert client.get("/").json()["message"].startswith("Service is running")
