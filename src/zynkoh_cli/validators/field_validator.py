"""
Validation for --fields specifications (Section 7, Section 21).

Parses and validates strings like:
    "code:str,name:str,email:str,department_id:uuid"

into a list of FieldSpec objects, rejecting invalid types and reserved
names before any file is generated.
"""

from __future__ import annotations

from zynkoh_cli.models.generation_context import FieldSpec

# The only field types the generator knows how to map to SQLAlchemy +
# Pydantic types. Deliberately small and explicit — an unsupported type
# should fail loudly at validation time, not produce broken generated code.
ALLOWED_FIELD_TYPES: set[str] = {
    "str",
    "int",
    "float",
    "decimal",
    "bool",
    "uuid",
    "datetime",
    "date",
    "text",
    "json",
}

# Reserved because they collide with base entity fields (tenant scoping,
# soft delete, audit) that every generated entity already gets for free.
# See Step 1, point 4 — these must never be redefined per-entity.
RESERVED_FIELD_NAMES: set[str] = {
    "id",
    "tenant_id",
    "created_at",
    "updated_at",
    "created_by",
    "updated_by",
    "is_deleted",
    "deleted_at",
    "deleted_by",
}


class FieldValidationError(ValueError):
    """Raised when a --fields specification is invalid."""


def parse_fields(raw: str | None) -> list[FieldSpec]:
    """
    Parse a raw '--fields' string into validated FieldSpec objects.

    Raises FieldValidationError with a clear message on any problem,
    rather than silently skipping or guessing.
    """
    if raw is None or not raw.strip():
        return []

    specs: list[FieldSpec] = []
    seen_names: set[str] = set()

    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue

        if ":" not in chunk:
            raise FieldValidationError(
                f"Invalid field definition '{chunk}'. "
                "Expected format 'name:type', e.g. 'email:str'."
            )

        name, _, field_type = chunk.partition(":")
        name = name.strip()
        field_type = field_type.strip().lower()

        nullable = False
        if field_type.endswith("?"):
            nullable = True
            field_type = field_type[:-1]

        _validate_field_name(name, seen_names)
        _validate_field_type(name, field_type)

        seen_names.add(name)
        specs.append(FieldSpec(name=name, type=field_type, nullable=nullable))

    return specs


def _validate_field_name(name: str, seen_names: set[str]) -> None:
    if not name:
        raise FieldValidationError("Field name cannot be empty.")

    if not name.replace("_", "").isalnum():
        raise FieldValidationError(
            f"Invalid field name '{name}'. "
            "Use lowercase letters, digits, and underscores only."
        )

    if not name[0].isalpha():
        raise FieldValidationError(
            f"Invalid field name '{name}'. Must start with a letter."
        )

    if name in RESERVED_FIELD_NAMES:
        raise FieldValidationError(
            f"Field name '{name}' is reserved — it's already provided by "
            "the base entity (tenant scoping, audit, or soft-delete fields). "
            "Choose a different name."
        )

    if name in seen_names:
        raise FieldValidationError(f"Duplicate field name '{name}'.")


def _validate_field_type(name: str, field_type: str) -> None:
    if field_type not in ALLOWED_FIELD_TYPES:
        allowed = ", ".join(sorted(ALLOWED_FIELD_TYPES))
        raise FieldValidationError(
            f"Invalid type '{field_type}' for field '{name}'. "
            f"Allowed types: {allowed}."
        )