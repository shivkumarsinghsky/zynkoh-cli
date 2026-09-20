"""
zynkoh — Zynkoh internal developer CLI entrypoint.
"""

from __future__ import annotations

import typer

from zynkoh_cli.commands.create import create_app

app = typer.Typer(
    name="zynkoh",
    help="Zynkoh architecture and code generator CLI.",
    no_args_is_help=True,
)

app.add_typer(create_app)


if __name__ == "__main__":
    app()