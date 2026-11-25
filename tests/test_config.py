from pathlib import Path

import pytest
from pydantic import ValidationError

from template_sample_app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _fresh_settings() -> None:
    get_settings.cache_clear()


def test_rejects_unknown_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(log_level="LOUD")  # type: ignore[arg-type]


def test_rejects_privileged_port() -> None:
    with pytest.raises(ValidationError):
        Settings(http_port=80)


def test_reads_matching_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env.test").write_text("APP_TITLE=from-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("APP_TITLE", raising=False)
    assert get_settings().app_title == "from-file"


def test_real_environment_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env.test").write_text("APP_TITLE=from-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_TITLE", "from-env")
    assert get_settings().app_title == "from-env"


def test_invalid_environment_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "NOPE")
    with pytest.raises(ValidationError):
        get_settings()


def test_blank_values_use_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # An env file carried over from an older project often has names with blank values.
    (tmp_path / ".env.test").write_text("APP_TITLE=\nAPP_VERSION=\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("APP_TITLE", raising=False)
    monkeypatch.delenv("APP_VERSION", raising=False)
    settings = get_settings()
    assert settings.app_title == Settings.model_fields["app_title"].default
    assert settings.app_version == Settings.model_fields["app_version"].default


def test_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        Settings(app_title="")
