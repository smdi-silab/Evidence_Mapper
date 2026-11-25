"""Command-line entry point: `evidence-mapper`."""

import logging
from typing import Annotated

import typer

from evidence_mapper import __version__
from evidence_mapper.config import REQUIRED_FIELDS, Settings
from evidence_mapper.log import configure_logging

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="evidence-mapper",
    help="Regulatory Evidence Mapper: feasibility-spike pipeline.",
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(help="Inspect configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"evidence-mapper {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_print_version,
            is_eager=True,
            help="Show the package version and exit.",
        ),
    ] = False,
) -> None:
    """Regulatory Evidence Mapper: feasibility-spike pipeline."""
    settings = Settings()
    configure_logging(settings)
    ctx.obj = settings


@config_app.command("check")
def config_check(ctx: typer.Context) -> None:
    """List each setting as set or not set. Exit 1 if a required one is missing.

    Values are shown only for settings that aren't secret.
    """
    settings: Settings = ctx.obj
    width = max(len(name) for name in Settings.env_names())
    for field in Settings.model_fields:
        value = getattr(settings, field)
        if value is None:
            shown = "not set"
        elif Settings.is_secret(field):
            shown = "set"
        else:
            shown = str(value)
        typer.echo(f"{Settings.env_name(field):<{width}}  {shown}")

    missing = settings.missing(*REQUIRED_FIELDS)
    logger.info(
        "config check: %d settings, %d required missing", len(Settings.model_fields), len(missing)
    )
    if missing:
        typer.echo(f"Missing required setting(s): {', '.join(missing)}", err=True)
        raise typer.Exit(code=1)
    typer.echo("All required settings are set.")


def main() -> None:
    app()
