"""Settings, read only from environment variables (spec 001, FR-4; SP-04).

Settings load without error when a value is missing. Code that needs a setting calls
`Settings.require(...)`, which fails with the variable's name and never its value.
Settings never read a `.env` file; use `uv run --env-file .env ...` for local convenience.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# pipeline/src/evidence_mapper/config.py -> repository root (editable install assumed).
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "data"

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class MissingSettingError(Exception):
    """A required setting is not set. The message names variables, never values."""

    def __init__(self, env_names: list[str]) -> None:
        self.env_names = env_names
        super().__init__(f"Missing required setting(s): {', '.join(env_names)}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, env_ignore_empty=True, extra="ignore")

    regulations_gov_api_key: SecretStr | None = Field(
        default=None, validation_alias="REGULATIONS_GOV_API_KEY"
    )
    aws_profile: str | None = Field(default=None, validation_alias="AWS_PROFILE")
    data_dir: Path = Field(default=DEFAULT_DATA_DIR, validation_alias="EVIDENCE_MAPPER_DATA_DIR")
    log_level: LogLevel = Field(default="INFO", validation_alias="EVIDENCE_MAPPER_LOG_LEVEL")

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @classmethod
    def env_name(cls, field: str) -> str:
        alias = cls.model_fields[field].validation_alias
        assert isinstance(alias, str)
        return alias

    @classmethod
    def env_names(cls) -> list[str]:
        return [cls.env_name(field) for field in cls.model_fields]

    @classmethod
    def is_secret(cls, field: str) -> bool:
        return field in SECRET_FIELDS

    def missing(self, *fields: str) -> list[str]:
        """Environment names of the given fields that are not set."""
        return [self.env_name(f) for f in fields if getattr(self, f) is None]

    def require(self, *fields: str) -> None:
        """Raise MissingSettingError naming any of the given fields that are not set."""
        missing = self.missing(*fields)
        if missing:
            raise MissingSettingError(missing)

    def secret_values(self) -> list[str]:
        """Plain values of secret settings that are set, for log redaction only."""
        values = []
        for field in SECRET_FIELDS:
            value = getattr(self, field)
            if isinstance(value, SecretStr) and value.get_secret_value():
                values.append(value.get_secret_value())
        return values


SECRET_FIELDS: frozenset[str] = frozenset({"regulations_gov_api_key"})

# Settings the pipeline needs before any stage can run. `config check` fails if one is missing.
REQUIRED_FIELDS: tuple[str, ...] = ("regulations_gov_api_key",)
