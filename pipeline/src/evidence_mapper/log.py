"""Logging setup (SP-01, ADR 0011).

Log only IDs, hashes, token counts, timings and errors. Never log comment text, prompts
that contain it, or model outputs. The redaction filter below is a backstop for secret
settings only; it does not make it safe to log comment text.
"""

import logging
import sys
from typing import TextIO

from evidence_mapper.config import Settings

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_HANDLER_NAME = "evidence-mapper"


class RedactSecretsFilter(logging.Filter):
    """Replace any secret setting's value with `***` in formatted log messages."""

    def __init__(self, secrets: list[str]) -> None:
        super().__init__()
        self._secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        if self._secrets:
            message = record.getMessage()
            for secret in self._secrets:
                message = message.replace(secret, "***")
            record.msg = message
            record.args = None
        return True


def configure_logging(settings: Settings, stream: TextIO | None = None) -> None:
    """Send logs to stderr (or `stream`) with secret redaction. Safe to call repeatedly."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if handler.get_name() == _HANDLER_NAME:
            root.removeHandler(handler)
    handler = logging.StreamHandler(stream if stream is not None else sys.stderr)
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(RedactSecretsFilter(settings.secret_values()))
    root.addHandler(handler)
    root.setLevel(settings.log_level)
