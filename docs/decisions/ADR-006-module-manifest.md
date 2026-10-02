# ADR-006: Module manifest as the source of truth

## Context
Platform concerns such as RBAC seeding, API gateway routing and event catalogues need to know
which permissions, routes and events each module exposes. Scraping the code for this is
unreliable.

## Decision
Every module has a `module.yaml` (`ModuleManifest`, Pydantic) recording its permissions, events,
routes, dependencies and generator template version. `feature` and `crud` update it as they add
resources; the manifest is merged mechanically, not rendered from a template.

## Alternatives
- **Derive metadata from OpenAPI at runtime:** covers routes but not permissions or events.
- **Central registry file for all modules:** creates merge conflicts between teams.

## Trade-offs
Hand-written endpoints must be added to the manifest manually.

## Consequences
Platform tooling can read one file per module to configure permissions and routing.
