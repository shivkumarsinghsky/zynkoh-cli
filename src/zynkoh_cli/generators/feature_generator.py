"""
FeatureGenerator: builds a full vertical slice for an entity inside an
existing module (Section 6) — domain entity/repository/service/events,
application commands/queries/handlers, infrastructure repository
implementation, Pydantic schemas, FastAPI router, and test stubs.

Also updates the module's existing module.yaml manifest with the new
permissions, route, and events this feature introduces.
"""

from __future__ import annotations

from pathlib import Path

from zynkoh_cli.generators.base_generator import BaseGenerator, PlannedFile
from zynkoh_cli.models.manifest import ModuleManifest


class FeatureGenerator(BaseGenerator):
    def __init__(self, *args, module_path: Path, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.module_path = module_path

    def plan_files(self) -> list[PlannedFile]:
        entity = self.context.entity.snake  # type: ignore[union-attr]
        app = self.module_path / "app"

        return [
            PlannedFile(
                "v1/entity/domain_entity.py.j2",
                app / "domain" / "entities" / f"{entity}.py",
            ),
            PlannedFile(
                "v1/entity/repository_interface.py.j2",
                app / "domain" / "repositories" / f"{entity}_repository.py",
            ),
            PlannedFile(
                "v1/feature/domain_service.py.j2",
                app / "domain" / "services" / f"{entity}_service.py",
            ),
            PlannedFile(
                "v1/feature/domain_events.py.j2",
                app / "domain" / "events" / f"{entity}_events.py",
            ),
            PlannedFile(
                "v1/feature/command_create.py.j2",
                app / "application" / "commands" / f"create_{entity}.py",
            ),
            PlannedFile(
                "v1/feature/command_update.py.j2",
                app / "application" / "commands" / f"update_{entity}.py",
            ),
            PlannedFile(
                "v1/feature/command_delete.py.j2",
                app / "application" / "commands" / f"delete_{entity}.py",
            ),
            PlannedFile(
                "v1/feature/query_get.py.j2",
                app / "application" / "queries" / f"get_{entity}.py",
            ),
            PlannedFile(
                "v1/feature/query_list.py.j2",
                app / "application" / "queries" / f"list_{entity}.py",
            ),
            PlannedFile(
                "v1/feature/handlers_facade.py.j2",
                app / "application" / "handlers" / f"{entity}_handlers.py",
            ),
            PlannedFile(
                "v1/feature/persistence_model.py.j2",
                app / "infrastructure" / "persistence" / "models" / f"{entity}_model.py",
            ),
            PlannedFile(
                "v1/feature/repository_impl.py.j2",
                app / "infrastructure" / "persistence" / f"{entity}_repository_impl.py",
            ),
            PlannedFile(
                "v1/feature/schema_request.py.j2",
                app / "schemas" / f"{entity}_request.py",
            ),
            PlannedFile(
                "v1/feature/schema_response.py.j2",
                app / "schemas" / f"{entity}_response.py",
            ),
            PlannedFile(
                "v1/feature/router.py.j2",
                app / "api" / f"{entity}_router.py",
            ),
            PlannedFile(
                "v1/feature/test_unit.py.j2",
                self.module_path / "tests" / "unit" / f"test_{entity}_domain.py",
            ),
            PlannedFile(
                "v1/feature/test_integration.py.j2",
                self.module_path / "tests" / "integration" / f"test_{entity}_repository.py",
            ),
            PlannedFile(
                "v1/feature/test_contract.py.j2",
                self.module_path / "tests" / "contract" / f"test_{entity}_api.py",
            ),
            PlannedFile(
                "v1/feature/migration_placeholder.txt.j2",
                self.module_path / "migrations" / f"{entity}_PLACEHOLDER.txt",
            ),
        ]

    def plan_extra_files(self) -> list[tuple[Path, str]]:
        manifest_path = self.module_path / "module.yaml"
        manifest = ModuleManifest.from_yaml(manifest_path.read_text(encoding="utf-8"))

        ctx = self.context
        prefix = ctx.permission_prefix
        entity_pascal = ctx.entity.pascal  # type: ignore[union-attr]

        manifest.add_permission(f"{prefix}.read")
        manifest.add_permission(f"{prefix}.create")
        manifest.add_permission(f"{prefix}.update")
        manifest.add_permission(f"{prefix}.delete")

        manifest.add_event(f"{entity_pascal}Created")
        manifest.add_event(f"{entity_pascal}Updated")
        manifest.add_event(f"{entity_pascal}Deleted")

        manifest.add_route(ctx.api_path, ["GET", "POST", "PUT", "DELETE"])

        return [(manifest_path, manifest.to_yaml())]

    def plan_appends(self) -> list[tuple[Path, str, str]]:
        entity = self.context.entity.snake  # type: ignore[union-attr]
        router_path = self.module_path / "app" / "api" / "router.py"

        import_line = (
            f"from app.api.{entity}_router import router as {entity}_router"
        )
        include_line = f"router.include_router({entity}_router)"

        append_block = f"{import_line}\n{include_line}"

        return [(router_path, import_line, append_block)]