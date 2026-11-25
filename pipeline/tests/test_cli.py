import shutil
import subprocess

from typer.testing import CliRunner

from evidence_mapper import __version__
from evidence_mapper.cli import app

runner = CliRunner()


def test_ac1_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "evidence-mapper" in result.output or "Usage" in result.output


def test_ac1_entry_point_help() -> None:
    """AC-1: the installed `evidence-mapper` script runs and exits 0."""
    exe = shutil.which("evidence-mapper")
    assert exe is not None, "evidence-mapper entry point not installed; run `uv sync`"
    result = subprocess.run([exe, "--help"], capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_ac2_version_prints_package_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"evidence-mapper {__version__}"
    assert __version__ == "0.1.0"
