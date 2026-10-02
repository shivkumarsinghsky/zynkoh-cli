"""
`zynkoh create module <name>` command.

This file is intentionally thin: parse CLI args/options, build a
GenerationContext, delegate to ModuleGenerator, and translate results
into a process exit code. No generation logic lives here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from zynkoh_cli.generators.module_generator import ModuleGenerator
from zynkoh_cli.models.generation_context import GenerationContext, NamingVariants
from zynkoh_cli.validators.module_validator import (
    ModuleValidationError,
    validate_module_does_not_exist,
    validate_name,
)

console = Console()

# Project root is resolved relative to where `zynkoh` is invoked, since
# it's meant to be run from inside a Zynkoh backend repo checkout.
DEFAULT_MODULES_ROOT = Path.cwd() / "apps" / "modules"


def create_module(
    name: Annotated[
        str | None,
        typer.Argument(help="Module name, e.g. hrms, crm, work-order-management"),
    ] = None,
    tenant_aware: Annotated[
        bool,
        typer.Option(
            "--tenant-aware/--no-tenant-aware",
            help="Whether this module's entities are tenant-scoped by default.",
        ),
    ] = True,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be generated without writing files."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing files."),
    ] = False,
    modules_root: Annotated[
        Path,
        typer.Option(
            "--modules-root",
            help="Root directory for modules (default: ./apps/modules).",
        ),
    ] = DEFAULT_MODULES_ROOT,
) -> None:
    """Generate a complete bounded-context module skeleton."""
    try:
        if name is None:
            name = typer.prompt("Module name")
            tenant_aware = typer.confirm("Tenant aware?", default=tenant_aware)
            dry_run = typer.confirm("Dry run (preview only)?", default=dry_run)
            force = typer.confirm("Overwrite existing files if present?", default=force)

        validate_name(name, kind="module name")

        module_variants = NamingVariants.from_raw(name)

        if not dry_run and not force:
            validate_module_does_not_exist(module_variants.snake, modules_root)

        context = GenerationContext(
            module=module_variants,
            tenant_aware=tenant_aware,
        )

        generator = ModuleGenerator(
            context,
            dry_run=dry_run,
            force=force,
            modules_root=modules_root,
        )
        results = generator.generate()

        if generator.has_conflicts(results):
            console.print(
                "\n[bold red]Generation stopped due to conflicts.[/bold red] "
                "No new files were affected beyond what's shown above."
            )
            raise typer.Exit(code=1)

        if not dry_run:
            console.print(
                f"\n[bold green]Module '{module_variants.snake}' generated "
                f"at {modules_root / module_variants.snake}[/bold green]"
            )

    except ModuleValidationError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e