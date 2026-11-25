import pytest
from fastapi.testclient import TestClient

from template_sample_app.config import Settings
from template_sample_app.main import create_app

client = TestClient(create_app(Settings(app_env="test", log_json=True)))


def test_live_reports_ok() -> None:
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_reports_service_metadata() -> None:
    body = client.get("/health/ready").json()
    assert body["status"] == "ready"
    assert body["env"] == "test"
    assert body["timestamp_utc"].endswith("+00:00")


def test_root() -> None:
    assert client.get("/").json()["message"].startswith("Service is running")


def test_request_id_is_echoed_when_safe() -> None:
    r = client.get("/health/live", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"


def test_request_id_is_generated_when_missing() -> None:
    rid = client.get("/health/live").headers["X-Request-ID"]
    assert len(rid) == 32


@pytest.mark.parametrize(
    "unsafe",
    ["has space", "a" * 65, "<script>", "semi;colon", 'quote"d', "bad id\nwith-injection", ""],
)
def test_request_id_rejects_unsafe_values(unsafe: str) -> None:
    rid = client.get("/health/live", headers={"X-Request-ID": unsafe}).headers["X-Request-ID"]
    assert rid != unsafe
    assert len(rid) == 32


def test_api_docs_hidden_in_prod() -> None:
    prod = TestClient(create_app(Settings(app_env="prod", log_json=True)))
    assert prod.get("/docs").status_code == 404
    assert prod.get("/openapi.json").status_code == 404
    assert client.get("/openapi.json").status_code == 200
