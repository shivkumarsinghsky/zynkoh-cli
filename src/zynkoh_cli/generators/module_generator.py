"""
ModuleGenerator: builds a complete bounded-context module skeleton
(Section 4) at apps/modules/<module_name>/.
"""

from __future__ import annotations

from pathlib import Path

from zynkoh_cli.generators.base_generator import BaseGenerator, PlannedFile
from zynkoh_cli.models.manifest import ModuleManifest

# Package directories that need an __init__.py but have no templated
# content of their own yet — they're populated later by
# feature/crud/entity commands, but must exist as valid packages now.
_EMPTY_PACKAGE_DIRS: list[str] = [
    "app",
    "app/api",
    "app/application",
    "app/application/commands",
    "app/application/queries",
    "app/application/handlers",
    "app/domain",
    "app/domain/entities",
    "app/domain/value_objects",
    "app/domain/repositories",
    "app/domain/services",
    "app/domain/events",
    "app/infrastructure",
    "app/infrastructure/persistence",
    "app/infrastructure/persistence/models",
    "app/infrastructure/messaging",
    "app/infrastructure/cache",
    "app/infrastructure/external",
    "app/schemas",
    "app/config",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]


class ModuleGenerator(BaseGenerator):
    def __init__(self, *args, modules_root: Path, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.modules_root = modules_root
        self.module_path = modules_root / self.context.module.snake

    def plan_files(self) -> list[PlannedFile]:
        base = "v1/module"
        out = self.module_path

        return [
            PlannedFile(f"{base}/app/main.py.j2", out / "app" / "main.py"),
            PlannedFile(
                f"{base}/app/api/router.py.j2", out / "app" / "api" / "router.py"
            ),
            PlannedFile(
                f"{base}/app/api/dependencies.py.j2",
                out / "app" / "api" / "dependencies.py",
            ),
            PlannedFile(
                f"{base}/app/config/settings.py.j2",
                out / "app" / "config" / "settings.py",
            ),
            PlannedFile(
                f"{base}/app/infrastructure/persistence/base.py.j2",
                out / "app" / "infrastructure" / "persistence" / "base.py",
            ),
            PlannedFile(f"{base}/Dockerfile.j2", out / "Dockerfile"),
            PlannedFile(f"{base}/pyproject.toml.j2", out / "pyproject.toml"),
            PlannedFile(f"{base}/README.md.j2", out / "README.md"),
        ]

    def plan_extra_files(self) -> list[tuple[Path, str]]:
        extras: list[tuple[Path, str]] = []

        for rel_dir in _EMPTY_PACKAGE_DIRS:
            extras.append((self.module_path / rel_dir / "__init__.py", ""))

        extras.append((self.module_path / "migrations" / ".gitkeep", ""))

        manifest = self._build_manifest()
        extras.append((self.module_path / "module.yaml", manifest.to_yaml()))

        return extras

    def _build_manifest(self) -> ModuleManifest:
        ctx = self.context
        return ModuleManifest(
            name=ctx.module.human,
            code=ctx.module.snake,
            description=f"{ctx.module.human} module",
            module_type="business",
            database_schema=ctx.module.snake,
            tenant_strategy="shared" if ctx.tenant_aware else "none",
        )