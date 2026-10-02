"""
ModuleManifest: schema for module.yaml.

Every generated module gets a module.yaml built from this
model. This is a *declarative description* of the module for the future
SaaS Platform Module Manager — the CLI only ever writes this file, it
never reads or acts on tenant activation state (that's explicitly a
separate system, per the top-level instructions).
"""

from __future__ import annotations

from datetime import UTC, datetime

import yaml
from pydantic import BaseModel, Field


class RouteDescriptor(BaseModel):
    path: str
    methods: list[str]


class EventDescriptor(BaseModel):
    name: str
    version: int = 1


class ModuleManifest(BaseModel):
    name: str
    code: str
    version: str = "0.1.0"
    description: str = ""
    module_type: str = "business"  # "business" | "platform" | "integration"

    dependencies: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    events: list[EventDescriptor] = Field(default_factory=list)
    routes: list[RouteDescriptor] = Field(default_factory=list)

    database_schema: str
    enabled: bool = True

    tenant_strategy: str = "shared"  # "shared" | "none"
    migration_version: str | None = None
    generator_template_version: str = "v1"

    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    def to_yaml(self) -> str:
        """Serialize to YAML in a stable, human-friendly field order."""
        data = self.model_dump(exclude_none=True)
        return str(yaml.dump(data, sort_keys=False, default_flow_style=False))

    @classmethod
    def from_yaml(cls, content: str) -> ModuleManifest:
        data = yaml.safe_load(content)
        return cls(**data)

    def add_permission(self, permission: str) -> None:
        if permission not in self.permissions:
            self.permissions.append(permission)

    def add_event(self, name: str, version: int = 1) -> None:
        if not any(e.name == name for e in self.events):
            self.events.append(EventDescriptor(name=name, version=version))

    def add_route(self, path: str, methods: list[str]) -> None:
        self.routes.append(RouteDescriptor(path=path, methods=methods))