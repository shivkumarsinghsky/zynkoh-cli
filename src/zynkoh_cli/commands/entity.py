"""
`zynkoh create entity <name> --module <module>` command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from zynkoh_cli.generators.entity_generator import EntityGenerator
from zynkoh_cli.models.generation_context import GenerationContext, NamingVariants
from zynkoh_cli.validators.field_validator import FieldValidationError, parse_fields
from zynkoh_cli.validators.module_validator import (
    ModuleValidationError,
    validate_entity_does_not_exist,
    validate_module_exists,
    validate_name,
)

console = Console()

DEFAULT_MODULES_ROOT = Path.cwd() / "apps" / "modules"


def create_entity(
    name: Annotated[
        str | None, typer.Argument(help="Entity name, e.g. employee, work-order")
    ] = None,
    module: Annotated[
        str | None, typer.Option("--module", help="Target module, e.g. hrms")
    ] = None,
    tenant_aware: Annotated[
        bool,
        typer.Option("--tenant-aware/--no-tenant-aware"),
    ] = True,
    fields: Annotated[
        str | None,
        typer.Option(
            "--fields",
            help='Comma-separated fields, e.g. "code:str,name:str,department_id:uuid?"',
        ),
    ] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
    modules_root: Annotated[Path, typer.Option("--modules-root")] = DEFAULT_MODULES_ROOT,
) -> None:
    """Generate a domain entity + repository interface inside an existing module."""
    try:
        if name is None:
            name = typer.prompt("Entity name")
            module = typer.prompt("Target module", default=module or "")
            tenant_aware = typer.confirm("Tenant aware?", default=tenant_aware)
            fields = typer.prompt(
                "Fields (comma-separated, e.g. code:str,name:str) or blank for none",
                default=fields or "",
            ) or None
            dry_run = typer.confirm("Dry run (preview only)?", default=dry_run)
            force = typer.confirm("Overwrite existing files if present?", default=force)

        if not module:
            raise ModuleValidationError("--module is required.")

        validate_name(name, kind="entity name")
        validate_name(module, kind="module name")

        module_variants = NamingVariants.from_raw(module)
        entity_variants = NamingVariants.from_raw(name)

        module_path = validate_module_exists(module_variants.snake, modules_root)

        if not dry_run and not force:
            validate_entity_does_not_exist(entity_variants.snake, module_path)

        field_specs = parse_fields(fields)

        context = GenerationContext(
            module=module_variants,
            entity=entity_variants,
            tenant_aware=tenant_aware,
            fields=field_specs,
        )

        generator = EntityGenerator(
            context,
            dry_run=dry_run,
            force=force,
            module_path=module_path,
        )
        results = generator.generate()

        if generator.has_conflicts(results):
            console.print("\n[bold red]Generation stopped due to conflicts.[/bold red]")
            raise typer.Exit(code=1)

        if not dry_run:
            console.print(
                f"\n[bold green]Entity '{entity_variants.snake}' generated in "
                f"module '{module_variants.snake}'[/bold green]"
            )

    except (ModuleValidationError, FieldValidationError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e