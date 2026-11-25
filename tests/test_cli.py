from typer.testing import CliRunner

from template_sample_app.cli import app

runner = CliRunner()


def test_version_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "0.1.0"


def test_config_prints_validated_settings() -> None:
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert '"app_env"' in result.stdout
