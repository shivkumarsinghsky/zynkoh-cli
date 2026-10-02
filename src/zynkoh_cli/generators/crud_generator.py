"""
CrudGenerator: full CRUD with filtering/sorting/pagination.

Subclasses FeatureGenerator and overrides only the files that differ:
the list query, the repository interface/impl (filter/sort-aware `list`),
and the router (query params for filter/sort). Everything else — entity,
repository interface base shape, service, events, create/update/delete
commands, get query, schemas, tests, manifest updates, router mounting —
is identical to `feature` and is inherited unchanged.
"""

from __future__ import annotations

from zynkoh_cli.generators.base_generator import PlannedFile
from zynkoh_cli.generators.feature_generator import FeatureGenerator


class CrudGenerator(FeatureGenerator):
    def plan_files(self) -> list[PlannedFile]:
        planned = super().plan_files()
        entity = self.context.entity.snake  # type: ignore[union-attr]
        app = self.module_path / "app"

        overrides = {
            app / "domain" / "repositories" / f"{entity}_repository.py":
                "v1/crud/repository_interface.py.j2",
            app / "application" / "queries" / f"list_{entity}.py":
                "v1/crud/query_list.py.j2",
            app / "infrastructure" / "persistence" / f"{entity}_repository_impl.py":
                "v1/crud/repository_impl.py.j2",
            app / "api" / f"{entity}_router.py":
                "v1/crud/router.py.j2",
        }

        return [
            PlannedFile(overrides.get(p.output_path, p.template_relative_path), p.output_path)
            for p in planned
        ]