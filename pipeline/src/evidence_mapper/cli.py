"""Command-line entry point: `evidence-mapper`."""

from typing import Annotated

import typer

from evidence_mapper import __version__

app = typer.Typer(
    name="evidence-mapper",
    help="Regulatory Evidence Mapper: feasibility-spike pipeline.",
    no_args_is_help=True,
    add_completion=False,
)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"evidence-mapper {__version__}")
        raise typer.Exit()


@app.callback()
def root(
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


def main() -> None:
    app()
