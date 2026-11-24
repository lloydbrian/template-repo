from pathlib import Path

import pytest

from template_sample_app.config import load_env


def test_load_env_reads_matching_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env.test").write_text("SAMPLE_FLAG=on\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("SAMPLE_FLAG", raising=False)
    assert load_env() == "test"
    import os

    assert os.environ["SAMPLE_FLAG"] == "on"


def test_real_environment_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env.dev").write_text("SAMPLE_FLAG=file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("SAMPLE_FLAG", "env")
    load_env()
    import os

    assert os.environ["SAMPLE_FLAG"] == "env"
