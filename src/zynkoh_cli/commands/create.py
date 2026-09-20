"""
`zynkoh create` command group.
"""

from __future__ import annotations

import typer

from zynkoh_cli.commands.crud import create_crud
from zynkoh_cli.commands.entity import create_entity
from zynkoh_cli.commands.feature import create_feature
from zynkoh_cli.commands.module import create_module

create_app = typer.Typer(
    name="create",
    help="Generate architecture-compliant modules, features, and CRUD resources.",
    no_args_is_help=True,
)

create_app.command("module")(create_module)
create_app.command("entity")(create_entity)
create_app.command("feature")(create_feature)
create_app.command("crud")(create_crud)