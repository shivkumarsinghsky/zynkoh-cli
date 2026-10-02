"""
Validation for module/entity/feature names.

Checks Python-identifier safety, reserved keywords, and duplicate
module/entity detection against the existing apps/ directory tree.
"""

from __future__ import annotations

import keyword
import re
from pathlib import Path

from zynkoh_cli.utils import naming

# Reserved because they'd collide with Python stdlib, FastAPI internals,
# or Zynkoh's own shared-kernel package names.
RESERVED_NAMES: set[str] = {
    "test",
    "tests",
    "app",
    "apps",
    "core",
    "shared",
    "platform",
    "config",
    "models",
    "schemas",
    "api",
    "admin",
    "auth",
}

_VALID_RAW_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9\-_]*$")


class ModuleValidationError(ValueError):
    """Raised when a module/entity/feature name fails validation."""


def validate_name(raw: str, *, kind: str = "name") -> None:
    """
    Validate a raw name (before casing conversion) for basic safety.

    `kind` is used only to produce clearer error messages, e.g.
    "module name" vs "entity name".
    """
    if not raw or not raw.strip():
        raise ModuleValidationError(f"{kind.capitalize()} cannot be empty.")

    if not _VALID_RAW_NAME_PATTERN.match(raw):
        raise ModuleValidationError(
            f"Invalid {kind} '{raw}'. Must start with a letter and contain "
            "only letters, digits, hyphens, and underscores."
        )

    snake = naming.to_snake_case(raw)

    if keyword.iskeyword(snake):
        raise ModuleValidationError(
            f"'{raw}' is a reserved Python keyword and cannot be used as "
            f"a {kind}."
        )

    if snake in RESERVED_NAMES:
        raise ModuleValidationError(
            f"'{raw}' is a reserved name and cannot be used as a {kind}. "
            f"Reserved names: {', '.join(sorted(RESERVED_NAMES))}."
        )

    if not snake.isidentifier():
        raise ModuleValidationError(
            f"'{raw}' does not produce a valid Python identifier "
            f"(resolved to '{snake}')."
        )


def validate_module_does_not_exist(
    module_snake: str, modules_root: Path
) -> None:
    """
    Raise if apps/modules/<module_snake> already exists.

    Called by `zynkoh create module`. Not called by feature/crud/entity
    generators, which are *expected* to target an existing module.
    """
    module_path = modules_root / module_snake
    if module_path.exists():
        raise ModuleValidationError(
            f"Module '{module_snake}' already exists at {module_path}. "
            "Use a different name, or run feature/crud/entity generators "
            "against the existing module instead."
        )


def validate_module_exists(module_snake: str, modules_root: Path) -> Path:
    """
    Raise if apps/modules/<module_snake> does NOT exist.

    Called by `feature`/`crud`/`entity` generators, which require an
    existing module to generate into. Returns the module path on success.
    """
    module_path = modules_root / module_snake
    if not module_path.exists():
        raise ModuleValidationError(
            f"Module '{module_snake}' does not exist at {module_path}. "
            f"Run 'zynkoh create module {module_snake}' first."
        )
    return module_path


def validate_entity_does_not_exist(
    entity_snake: str, module_path: Path
) -> None:
    """
    Raise if a domain entity file already exists for this name inside
    the target module — prevents accidental duplicate CRUD generation.
    """
    entity_file = (
        module_path / "app" / "domain" / "entities" / f"{entity_snake}.py"
    )
    if entity_file.exists():
        raise ModuleValidationError(
            f"Entity '{entity_snake}' already exists at {entity_file}. "
            "Use --force to regenerate, or choose a different name."
        )