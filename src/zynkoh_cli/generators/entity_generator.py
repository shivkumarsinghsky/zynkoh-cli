"""
EntityGenerator: builds just a domain entity + repository interface
(Section 22 describes this as a lighter-weight alternative to full CRUD —
useful for domain modeling before committing to a full vertical slice).
"""

from __future__ import annotations

from pathlib import Path

from zynkoh_cli.generators.base_generator import BaseGenerator, PlannedFile
from zynkoh_cli.models.manifest import ModuleManifest


class EntityGenerator(BaseGenerator):
    def __init__(self, *args, module_path: Path, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.module_path = module_path

    def plan_files(self) -> list[PlannedFile]:
        base = "v1/entity"
        entity_snake = self.context.entity.snake  # type: ignore[union-attr]
        app = self.module_path / "app"

        return [
            PlannedFile(
                f"{base}/domain_entity.py.j2",
                app / "domain" / "entities" / f"{entity_snake}.py",
            ),
            PlannedFile(
                f"{base}/repository_interface.py.j2",
                app / "domain" / "repositories" / f"{entity_snake}_repository.py",
            ),
        ]

    def update_manifest(self, manifest: ModuleManifest) -> None:
        # Entity generation alone adds no permissions/routes/events yet —
        # those come from `crud`/`feature` generators. This hook exists
        # for consistency and so future entity-level concerns (e.g. a
        # domain event on creation) have an obvious place to be added.
        return