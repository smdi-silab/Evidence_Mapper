import io
import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from evidence_mapper.cli import app
from evidence_mapper.config import DEFAULT_DATA_DIR, MissingSettingError, Settings
from evidence_mapper.log import configure_logging

ENV_EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"
SENTINEL = "sentinel-secret-value-3f9a1c"

runner = CliRunner()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in Settings.env_names():
        monkeypatch.delenv(name, raising=False)


def test_settings_load_without_any_variables() -> None:
    """FR-4: missing settings don't fail at load, so --help works on a fresh clone."""
    settings = Settings()
    assert settings.regulations_gov_api_key is None
    assert settings.data_dir == DEFAULT_DATA_DIR
    assert DEFAULT_DATA_DIR.parent.joinpath("pipeline", "pyproject.toml").exists()


def test_ac4_config_check_names_missing_key() -> None:
    result = runner.invoke(app, ["config", "check"])
    assert result.exit_code == 1
    assert "Missing required setting(s): REGULATIONS_GOV_API_KEY" in result.stderr


def test_ac4_require_names_variable_not_value(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(MissingSettingError, match="REGULATIONS_GOV_API_KEY"):
        Settings().require("regulations_gov_api_key")
    monkeypatch.setenv("REGULATIONS_GOV_API_KEY", SENTINEL)
    Settings().require("regulations_gov_api_key")


def test_ac4_secret_not_in_output_or_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REGULATIONS_GOV_API_KEY", SENTINEL)
    monkeypatch.setenv("EVIDENCE_MAPPER_LOG_LEVEL", "debug")
    result = runner.invoke(app, ["config", "check"])
    assert result.exit_code == 0
    assert SENTINEL not in result.stdout
    assert SENTINEL not in result.stderr
    assert "REGULATIONS_GOV_API_KEY" in result.stdout
    assert SENTINEL not in repr(Settings())

    # Backstop: a secret that reaches a log message is redacted.
    stream = io.StringIO()
    configure_logging(Settings(), stream=stream)
    logging.getLogger("evidence_mapper.test").warning("leaked key=%s", SENTINEL)
    assert SENTINEL not in stream.getvalue()
    assert "leaked key=***" in stream.getvalue()


def _env_example_names() -> set[str]:
    names = set()
    for line in ENV_EXAMPLE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line.split("=", 1)[0].strip())
    return names


def test_ac5_env_example_lists_every_setting() -> None:
    assert _env_example_names() == set(Settings.env_names())
