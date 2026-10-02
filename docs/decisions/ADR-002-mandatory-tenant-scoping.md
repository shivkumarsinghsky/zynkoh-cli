# ADR-002: Mandatory tenant scoping for feature and CRUD generators

## Context
The platform is multi-tenant, and the most damaging bug in such a system is one tenant
reading another tenant's data. The v1 templates thread `tenant_id` through commands, queries,
repository interfaces, repository implementations, routers and tests. A `--no-tenant-aware`
flag existed on every command, but only some templates honoured it: generating a CRUD resource
with it produced code that referenced an undefined `tenant_id` and failed at runtime.

## Decision
In template v1, `feature` and `crud` always generate tenant-scoped code. Passing
`--no-tenant-aware` to them fails fast with a clear error and exit code 1 before any file is
written. `module` and `entity`, whose templates handle both modes correctly, keep the option.
Repository `update` and `delete` also verify the row's tenant, not only `get` and `list`.

## Alternatives
- **Make every template support both modes:** doubles the conditional surface across a dozen templates for a rare use case.
- **Keep the flag and document the breakage:** generates broken code, which a generator must never do.

## Trade-offs
Truly global resources (for example, a country list) are written by hand or modelled with a
platform-level tenant.

## Consequences
Tenant isolation cannot be switched off by accident. If single-tenant resources become common,
support will be added in a new template version with tests for both modes.
