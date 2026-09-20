"""
GenerationContext: the single object passed into every Jinja2 template.

Generators build one of these per entity/feature/module by resolving the
raw developer input through utils.naming, then pass it straight to the
renderer. Templates only ever reference fields on this object — they never
call naming functions directly. This keeps naming logic in exactly one
place (utils/naming.py) and templates purely declarative.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from zynkoh_cli.utils import naming


class NamingVariants(BaseModel):
    """All casing/pluralization forms derived from one raw input name."""

    raw: str
    snake: str
    snake_plural: str
    pascal: str
    pascal_plural: str
    kebab: str
    kebab_plural: str
    camel: str
    human: str

    @classmethod
    def from_raw(cls, raw: str) -> NamingVariants:
        return cls(
            raw=raw,
            snake=naming.to_snake_case(raw),
            snake_plural=naming.to_snake_plural(raw),
            pascal=naming.to_pascal_case(raw),
            pascal_plural=naming.to_pascal_plural(raw),
            kebab=naming.to_kebab_case(raw),
            kebab_plural=naming.to_kebab_plural(raw),
            camel=naming.to_camel_case(raw),
            human=naming.to_human_readable(raw),
        )


class FieldSpec(BaseModel):
    """One field from a --fields 'name:type' definition (CRUD generator)."""

    name: str
    type: str  # e.g. "str", "int", "uuid", "bool", "datetime", "decimal"
    nullable: bool = False


class GenerationContext(BaseModel):
    """
    Everything a template needs to render one generated artifact
    (a module, a feature, or a CRUD resource).

    module_name: the owning module, e.g. "hrms" — always required, since
        even a bare `module` generation command names itself as its own
        module for manifest purposes.
    entity_name: the entity/feature being generated, e.g. "employee".
        None when generating a module itself (no single entity yet).
    """

    module: NamingVariants
    entity: NamingVariants | None = None

    tenant_aware: bool = True
    soft_delete: bool = True
    generate_tests: bool = True
    generate_events: bool = True
    generate_migration: bool = True
    generate_api: bool = True
    generate_permissions: bool = True
    generate_docker: bool = True

    fields: list[FieldSpec] = Field(default_factory=list)

    template_version: str = "v1"

    @property
    def permission_prefix(self) -> str:
        """e.g. 'hrms.employee' — used to build hrms.employee.read etc."""
        if self.entity is None:
            return self.module.snake
        return f"{self.module.snake}.{self.entity.snake}"

    @property
    def api_path(self) -> str:
        """e.g. '/api/v1/hrms/employees', '/api/v1/eam/work-orders'"""
        resource = self.entity.kebab_plural if self.entity else self.module.kebab
        return f"/api/v1/{self.module.kebab}/{resource}"