# zynkoh-cli

The Zynkoh internal developer CLI — an architecture-compliant code generator
for the Zynkoh multi-tenant SaaS platform.

`zynkoh` generates modules, domain entities, full vertical-slice features,
and complete CRUD resources, all following the same Clean/Hexagonal
architecture conventions every time. It exists so two developers can build
a large multi-tenant platform without hand-writing the same folder
structure, repository boilerplate, and API wiring for every resource.

## Installation

```bash
cd tools/zynkoh-cli
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Verify:
```bash
zynkoh --help
```

> Run `zynkoh` commands from your repo root (the directory containing
> `apps/`), not from inside `tools/zynkoh-cli/` — generated paths are
> resolved relative to your current directory.

## Commands

| Command | Produces |
|---|---|
| `zynkoh create module <name>` | A complete, runnable bounded-context module skeleton |
| `zynkoh create entity <name> --module <module>` | A domain entity + repository interface only, no API |
| `zynkoh create feature <name> --module <module>` | A full vertical slice: domain, application, infrastructure, API, tests |
| `zynkoh create crud <name> --module <module> --fields "..."` | Full CRUD with filtering, sorting, and pagination on top of `feature` |

All commands support:

- `--dry-run` — show what would be generated without writing anything
- `--force` — overwrite existing files (off by default; conflicts are never silent)
- `--tenant-aware` / `--no-tenant-aware` — tenant scoping (default: on)
- `--modules-root` — override where modules live (default: `./apps/modules`)

`feature` and `crud` additionally support:
- `--fields "name:type,name:type?"` — field definitions. Append `?` to a
  type to make it nullable. Supported types: `str`, `int`, `float`,
  `decimal`, `bool`, `uuid`, `datetime`, `date`, `text`, `json`.
- `--soft-delete` / `--no-soft-delete` (default: on)

`--fields` is **required** for `crud` (a CRUD resource with no fields isn't
meaningful) and optional for `feature`.

## Usage examples

```bash
# A new bounded-context module
zynkoh create module eam

# A lightweight domain entity, no API yet
zynkoh create entity asset --module eam

# A full vertical slice with fields
zynkoh create feature work-order --module eam \
  --fields "asset_id:uuid,description:text,status:str,scheduled_date:date?"

# Full CRUD with filtering/sorting/pagination
zynkoh create crud asset --module eam \
  --fields "code:str,name:str,category:str,serial_number:str?,purchase_cost:decimal?"

# Preview without writing files
zynkoh create crud invoice --module crm --fields "amount:decimal,status:str" --dry-run
```

## What gets generated

`zynkoh create module <name>` produces:

apps/modules/<name>/
├── app/
│ ├── main.py FastAPI app entrypoint
│ ├── api/ Root router, shared dependencies
│ ├── application/ commands/ queries/ handlers/
│ ├── domain/ entities/ value_objects/ repositories/ services/ events/
│ ├── infrastructure/ persistence/ messaging/ cache/ external/
│ ├── schemas/ Pydantic request/response models
│ └── config/ Settings
├── migrations/
├── tests/ unit/ integration/ contract/
├── Dockerfile
├── pyproject.toml
├── module.yaml Manifest: permissions, events, routes
└── README.md


`zynkoh create crud <entity> --module <name> --fields "..."` adds, per entity:
domain entity, repository interface + SQLAlchemy implementation, domain
service, domain events, create/update/delete commands, get/list (with
filter/sort) queries, a handlers facade, Pydantic request/response schemas,
a FastAPI router (mounted automatically into the module's root router),
unit/integration/contract test stubs, a migration placeholder, and updates
to `module.yaml` with the new permissions/events/route.

## Architecture principles the generator enforces

- **Domain entity ≠ persistence model.** Every entity is a plain dataclass
  with zero SQLAlchemy/FastAPI imports; a separate SQLAlchemy model and
  explicit mapper functions handle persistence. This is what allows a
  module to move to its own service later without rewriting business logic.
- **Tenant isolation at the repository layer.** Every tenant-aware
  repository method requires `tenant_id` as an argument — there is no
  method that queries without it, so a developer cannot forget to scope a
  query.
- **Capability-based permissions.** Generated permission strings
  (`hrms.employee.read`, etc.) carry no notion of roles — role-to-permission
  mapping is explicitly a platform-level concern, not generated per module.
- **No dynamic/unsafe SQL.** Filtering and sorting (`crud`) validate
  requested fields against a generated allowlist before ever building a
  query — column names are never taken directly from user input.
- **No cross-module imports.** Generated modules never import from each
  other's domain layers. Cross-module interaction is meant to happen via
  APIs, events, or a future shared-contracts package.

## Templates

Templates live under `src/zynkoh_cli/templates/v1/` and are versioned by
directory (Section 20). A future template revision would live alongside
this one as `v2/`, with `module.yaml`'s `generator_template_version` field
tracking which version a given module was generated with.

## Running the CLI's own tests

```bash
cd tools/zynkoh-cli
pytest
ruff check .
```

## Known limitations / TODOs in generated code

Generated modules intentionally contain a few stubs pointing at
not-yet-built shared platform packages:

- `app/api/dependencies.py`'s `get_db()` raises `NotImplementedError` —
  wire it to the shared platform's async session factory once that exists.
- `get_current_tenant_id()` resolves tenant from a raw `X-Tenant-Id`
  header — replace with real auth/tenant resolution once the shared auth
  package exists.
- Permission constants are generated but not enforced — RBAC enforcement
  is a platform-level concern, wired in separately.
- Domain event publishing is a `# TODO` comment in each command handler —
  wire to `platform.messaging` once Kafka/Redpanda integration exists.

These are deliberate — the generator produces the module's own code
correctly and completely; it does not (and should not) reach into
platform-level packages that don't exist yet.