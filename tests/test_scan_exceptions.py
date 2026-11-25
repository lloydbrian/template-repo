import importlib.util
from datetime import date
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "check_scan_exceptions", Path(__file__).parents[1] / "tools" / "check_scan_exceptions.py"
)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_valid_entry_passes(tmp_path: Path) -> None:
    f = tmp_path / ".trivyignore"
    f.write_text("CVE-2026-1  # reason: not reachable; owner: lbd; expires: 2026-02-01\n")
    assert _mod.check(f, today=date(2026, 1, 1)) == []


def test_expired_entry_fails(tmp_path: Path) -> None:
    f = tmp_path / ".trivyignore"
    f.write_text("CVE-2026-1  # reason: not reachable; owner: lbd; expires: 2025-01-01\n")
    assert "expired" in _mod.check(f, today=date(2026, 1, 1))[0]


def test_undocumented_entry_fails(tmp_path: Path) -> None:
    f = tmp_path / ".trivyignore"
    f.write_text("CVE-2026-1\n")
    assert "needs" in _mod.check(f)[0]


def test_far_future_expiry_fails(tmp_path: Path) -> None:
    f = tmp_path / ".trivyignore"
    f.write_text("CVE-2026-1  # reason: not reachable; owner: lbd; expires: 2099-01-01\n")
    assert "more than" in _mod.check(f, today=date(2026, 1, 1))[0]


def test_trivy_config_file_fails(tmp_path: Path) -> None:
    (tmp_path / "trivy.yaml").write_text("scan:\n  skip-dirs: [opt/venv]\n")
    assert "not allowed" in _mod.check(tmp_path / ".trivyignore")[0]


def test_trivy_env_override_fails(tmp_path: Path) -> None:
    (tmp_path / ".mise.toml").write_text('[env]\nTRIVY_SKIP_DIRS = "opt/venv"\n')
    assert "TRIVY_" in _mod.check(tmp_path / ".trivyignore")[0]


def test_undated_entry_fails_until_stamped(tmp_path: Path) -> None:
    f = tmp_path / ".pip-audit-ignore"
    f.write_text(
        '# new entries say "expires: on-bootstrap"\n'
        "PYSEC-2026-1  # reason: server only; owner: lbd; expires: on-bootstrap\n"
    )
    assert "not dated" in _mod.check(f, today=date(2026, 1, 1))[0]
    assert _mod.stamp(f, today=date(2026, 1, 1)) == 1
    assert "expires: 2026-04-01" in f.read_text()
    assert '# new entries say "expires: on-bootstrap"' in f.read_text()  # comment untouched
    assert _mod.check(f, today=date(2026, 1, 1)) == []
    assert _mod.stamp(f) == 0  # already dated: nothing changes


def test_pip_audit_args_only_for_documented_entries(tmp_path: Path) -> None:
    f = tmp_path / ".pip-audit-ignore"
    f.write_text(
        "# comment\n"
        "PYSEC-2026-1  # reason: server only; owner: lbd; expires: 2026-02-01\n"
        "PYSEC-2026-2\n"
    )
    assert _mod.pip_audit_args(f) == ["--ignore-vuln", "PYSEC-2026-1"]
    assert _mod.pip_audit_args(tmp_path / "missing") == []


def test_stamp_tolerates_spacing(tmp_path: Path) -> None:
    f = tmp_path / ".pip-audit-ignore"
    f.write_text("PYSEC-2026-1  # reason: server only; owner: lbd; expires:on-bootstrap\n")
    assert _mod.stamp(f, today=date(2026, 1, 1)) == 1
    assert _mod.check(f, today=date(2026, 1, 1)) == []
