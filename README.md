# zynkoh-cli

A production-grade developer CLI that generates architecture-compliant modules, domain entities, full vertical-slice features, and complete CRUD resources for the Zynkoh multi-tenant SaaS platform.

`zynkoh` exists so a small team can build a large, multi-tenant, eventually-microservices-ready platform without hand-writing the same folder structure, repository boilerplate, and API wiring for every new resource. Every generated module follows the same Clean/Hexagonal architecture conventions, every time — no drift between what one developer builds by hand and what another generates.

- [What it generates](#what-it-generates)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Architecture principles the generator enforces](#architecture-principles-the-generator-enforces)
- [Project structure](#project-structure)
- [Development setup](#development-setup)
- [Running tests](#running-tests)
- [Template system](#template-system)
- [Contributing](#contributing)
- [Known limitations](#known-limitations--todos-in-generated-code)
- [License](#license)

## What it generates

```bash
zynkoh create module hrms
zynkoh create crud employee --module hrms --fields "code:str,name:str,email:str,department_id:uuid?"
```

...produces a complete, runnable FastAPI module with tenant-scoped repositories, soft delete, audit fields, domain events, capability-based permissions, safe filtering/sorting, and test stubs — see [What gets generated](#what-gets-generated) below for the full picture.

## Installation

**Recommended — global tool install (isolated environment, no venv activation needed):**

```bash
uv tool install "git+https://github.com/shivkumarsinghsky/zynkoh-cli.git"
```

Verify:
```bash
zynkoh --help
```

Upgrade later:
```bash
uv tool upgrade zynkoh-cli
```

Uninstall:
```bash
uv tool uninstall zynkoh-cli
```

**Alternative — install into a project's own venv:**

```bash
uv pip install "git+https://github.com/shivkumarsinghsky/zynkoh-cli.git"
```

**Pinned to a specific release** (recommended for CI/CD, so a new tag can't silently change generated output mid-pipeline):

```bash
uv tool install "git+https://github.com/shivkumarsinghsky/zynkoh-cli.git@v1.0.0"
```

> `zynkoh` requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). If you don't have `uv` yet:
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```

## Quick start

Run `zynkoh` commands from the root of the backend repo you're generating *into* (the directory that should contain — or already contains — `apps/modules/`), not from inside this CLI's own repo.

```bash
cd /path/to/your-backend-repo

# Create a new bounded-context module
zynkoh create module eam

# Add a lightweight domain entity (no API yet)
zynkoh create entity asset --module eam

# Add a full vertical slice with fields
zynkoh create feature work-order --module eam \
  --fields "asset_id:uuid,description:text,status:str,scheduled_date:date?"

# Add full CRUD with filtering/sorting/pagination
zynkoh create crud asset --module eam \
  --fields "code:str,name:str,category:str,serial_number:str?,purchase_cost:decimal?"

# Preview any command without writing files
zynkoh create crud invoice --module crm --fields "amount:decimal,status:str" --dry-run
```

Run any `create` subcommand with no name given at all to be prompted interactively:

```bash
zynkoh create module
```

Then boot the generated module and try it:

```bash
cd apps/modules/eam
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` to see the generated API.

## Commands

| Command | Produces |
|---|---|
| `zynkoh create module <name>` | A complete, runnable bounded-context module skeleton |
| `zynkoh create entity <name> --module <module>` | A domain entity + repository interface only, no API |
| `zynkoh create feature <name> --module <module>` | A full vertical slice: domain, application, infrastructure, API, tests |
| `zynkoh create crud <name> --module <module> --fields "..."` | Full CRUD with filtering, sorting, and pagination on top of `feature` |

All commands support:

| Flag | Effect |
|---|---|
| `--dry-run` | Show what would be generated without writing anything |
| `--force` | Overwrite existing files (off by default; conflicts are never silent) |
| `--tenant-aware` / `--no-tenant-aware` | Tenant scoping (default: on) |
| `--modules-root` | Override where modules live (default: `./apps/modules`) |

`feature` and `crud` additionally support:

| Flag | Effect |
|---|---|
| `--fields "name:type,name:type?"` | Field definitions. Append `?` to a type for nullable. Types: `str`, `int`, `float`, `decimal`, `bool`, `uuid`, `datetime`, `date`, `text`, `json` |
| `--soft-delete` / `--no-soft-delete` | Soft-delete fields (default: on) |

`--fields` is **required** for `crud` (a CRUD resource with no fields isn't meaningful) and optional for `feature`.

Omit the name argument on any command to be prompted for every option interactively — this is the same code path as passing flags directly, so scripting and CI/CD usage are unaffected.

## Architecture principles the generator enforces

- **Domain entity ≠ persistence model.** Every entity is a plain dataclass with zero SQLAlchemy or FastAPI imports. A separate SQLAlchemy model plus explicit mapper functions handle persistence. This is what lets a module move to its own microservice later without rewriting business logic.
- **Tenant isolation at the repository layer.** Every tenant-aware repository method requires `tenant_id` as an argument. There is no method that can query without it — a developer cannot forget to scope a query, because the interface doesn't allow it.
- **Capability-based permissions.** Generated permission strings (e.g. `hrms.employee.read`) carry no notion of roles. Role-to-permission mapping is a platform-level concern, deliberately not generated per module.
- **No dynamic or unsafe SQL.** Filtering and sorting (`crud`) validate requested fields against a generated allowlist before ever building a query. Column names are never taken directly from user input.
- **No cross-module imports.** Generated modules never import from each other's domain layers. Cross-module interaction happens via APIs, events, or a future shared-contracts package.
- **Manifest as the source of truth.** Every module carries a `module.yaml` recording its permissions, events, routes, and dependencies — kept in sync automatically as `feature`/`crud` commands add to it.

## What gets generated

`zynkoh create module <name>`:

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


`zynkoh create crud <entity> --module <name> --fields "..."` additionally generates, per entity: a domain entity, a repository interface plus SQLAlchemy implementation, a domain service, domain events, create/update/delete commands, get/list (filter+sort aware) queries, a handlers facade, Pydantic request/response schemas, a FastAPI router (mounted automatically into the module's root router), unit/integration/contract test stubs, a migration placeholder, and an update to `module.yaml`.

## Project structure

This repository (the CLI itself, not anything it generates):
zynkoh-cli/
├── pyproject.toml
├── README.md
├── src/
│ └── zynkoh_cli/
│ ├── main.py Typer app entrypoint
│ ├── commands/ Thin CLI layer: parse args, call a generator, print output
│ ├── generators/ plan_files() based generation logic — no filesystem I/O of their own
│ ├── models/ GenerationContext, ModuleManifest (Pydantic)
│ ├── validators/ Name/field validation (Section 21-style checks)
│ ├── utils/ naming.py, file_writer.py, renderer.py
│ └── templates/
│ └── v1/ Jinja2 templates, versioned by directory
│ ├── module/
│ ├── entity/
│ ├── feature/
│ └── crud/
└── tests/
└── unit/


**Layering rule:** `commands/` is dumb (parse → call → print), `generators/` is smart (decide what to render and where), `templates/` is purely declarative. A generator's `plan_files()` method must be side-effect-free — it returns a list of (template, output path) pairs without touching disk, which is what makes generators testable in isolation and makes `--dry-run` a true preview rather than a partial run.

## Development setup

```bash
git clone https://github.com/shivkumarsinghsky/zynkoh-cli.git
cd zynkoh-cli
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Verify your editable install works:
```bash
zynkoh --help
```

Because it's an editable install, changes to `src/zynkoh_cli/**` — including template files — take effect immediately on the next `zynkoh` invocation, no reinstall needed.

## Running tests

```bash
pytest -v
ruff check .
```

Both must pass cleanly before opening a PR. The test suite covers the naming engine, both validators, `GenerationContext`'s computed properties, `ModuleManifest` round-tripping, and `ModuleGenerator`'s planning logic (asserting on `plan_files()` output directly, without touching a real filesystem, plus one real-write integration test using `tmp_path`).

If you add a new generator or extend an existing one, follow the pattern in `tests/unit/test_module_generator.py`: assert on the planned file list and manifest content directly, rather than asserting on rendered template *text*, which is brittle. Rendered-output correctness is better verified by actually generating into a scratch module and running it (see below).

### Manually verifying generated output

Automated tests cover planning logic; they intentionally don't render full templates end-to-end (that would mean re-implementing FastAPI/SQLAlchemy assertions inside the test suite). To verify a template change produces working code:

```bash
cd /tmp
mkdir zynkoh-manual-check && cd zynkoh-manual-check
zynkoh create module scratch
zynkoh create crud widget --module scratch --fields "name:str,price:decimal"
cd apps/modules/scratch
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Then hit the generated endpoints and check `/docs` renders correctly. Delete `/tmp/zynkoh-manual-check` when done.

## Template system

Templates live under `src/zynkoh_cli/templates/v1/` and are versioned by directory. Every rendered file has access to a single `context: GenerationContext` object (see `models/generation_context.py`) — templates never call naming functions directly; all casing/pluralization is resolved once, in Python, before rendering.

Key `context` fields used across templates:

| Field | Example |
|---|---|
| `context.module.snake` / `.pascal` / `.kebab` / `.human` | `hrms` / `HRMS` / `hrms` / `HRMS` |
| `context.entity.snake` / `.pascal` / `.kebab_plural` / `.human` | `work_order` / `WorkOrder` / `work-orders` / `Work Order` |
| `context.fields` | list of `FieldSpec(name, type, nullable)` |
| `context.tenant_aware` / `.soft_delete` | booleans controlling conditional blocks |
| `context.permission_prefix` | `hrms.employee` |
| `context.api_path` | `/api/v1/eam/work-orders` |

If you're adding a new template file to an existing generator's directory, you generally don't need to touch any Python — `TemplateRenderer.list_templates()` and each generator's `plan_files()` explicitly list which templates map to which output paths, so a new file needs a new `PlannedFile(...)` entry in the relevant `generators/*.py`, but no renderer changes.

If you're introducing a breaking change to an existing template's output shape, create a `v2/` directory alongside `v1/` rather than editing `v1/` in place — modules already generated under `v1` record `generator_template_version: v1` in their `module.yaml`, and existing modules should never be silently affected by a CLI upgrade.

## Contributing

1. **Fork and clone**, then follow [Development setup](#development-setup) above.
2. **Open an issue first** for anything beyond a small fix — especially new field types, new generator commands, or changes to what gets generated by default — so we can agree on the approach before you invest time in an implementation.
3. **Branch naming:** `feature/<short-description>` or `fix/<short-description>`.
4. **Before opening a PR:**
   - `pytest -v` passes
   - `ruff check .` passes with zero errors
   - If you changed or added a template, manually verify the generated output actually imports and runs (see [Manually verifying generated output](#manually-verifying-generated-output)) — a template that renders valid-looking text but produces a `TypeError` on import has shipped a real bug before, more than once, in this project's history. Don't rely on visual inspection of `.j2` files alone.
   - Add or update unit tests for any new validator rule, naming function, or generator planning logic.
5. **Commit messages:** short, imperative, and scoped — e.g. `crud: add datetime filter support`, `naming: fix irregular plural for "series"`.
6. **PR description should state:** what changed, why, and the exact commands you used to manually verify generated output (paste the terminal output if it's not obvious).

### Coding conventions

- Python 3.12+, full type hints, `from __future__ import annotations` at the top of every module.
- `commands/*.py` stay thin: parse → validate → build a `GenerationContext` → call a generator → report the result. No generation logic here.
- `generators/*.py` implement `plan_files()` (pure, no I/O) and optionally `plan_extra_files()` / `plan_appends()` for non-template-rendered or additive output (see `base_generator.py` for the contract).
- Validation errors raise `ModuleValidationError` or `FieldValidationError` with a clear, actionable message — never a bare `ValueError` or an unguarded exception that surfaces as a raw traceback to the CLI user.
- Never introduce a way for generated code to build SQL from unvalidated input — any new filter/sort/query capability must validate against an explicit, generated allowlist, matching the existing pattern in `templates/v1/crud/query_list.py.j2`.
- Run `ruff check .` before committing; the config in `pyproject.toml` is the source of truth for style (line length, import order, etc.) — don't fight it with inline `# noqa` unless there's a genuinely good reason, and explain that reason in a comment.

### Adding a new field type

To add a new `--fields` type (e.g. `email` as a distinct validated type):

1. Add it to `ALLOWED_FIELD_TYPES` in `validators/field_validator.py`.
2. Add its Python type mapping to the inline dict in every template that maps field types (`domain_entity.py.j2`, `command_create.py.j2`, `command_update.py.j2`, `schema_request.py.j2`, `schema_response.py.j2`, `persistence_model.py.j2` — search for `"decimal": "Decimal"` across `templates/` to find them all).
3. Add a test case to `tests/unit/test_field_validator.py`.
4. Manually generate a `crud` resource using the new type and confirm it imports and boots.

### Adding a new generator command (e.g. a future `zynkoh create worker`)

1. Add templates under `templates/v1/<name>/`.
2. Create `generators/<name>_generator.py` subclassing `BaseGenerator`, implementing `plan_files()` at minimum.
3. Create `commands/<name>.py` following the exact shape of `commands/entity.py` (validation → context → generator → result reporting → interactive prompt fallback).
4. Register it in `commands/create.py`.
5. Add planning-logic tests following `tests/unit/test_module_generator.py`'s pattern.
6. Update this README's [Commands](#commands) table and [What gets generated](#what-gets-generated) section.

## Known limitations / TODOs in generated code

Generated modules intentionally contain a few stubs pointing at not-yet-built shared platform packages — this is by design, not an oversight:

- `app/api/dependencies.py`'s `get_db()` raises `NotImplementedError` — wire it to your platform's async session factory.
- `get_current_tenant_id()` resolves tenant from a raw `X-Tenant-Id` header — replace with real auth/tenant resolution once your auth package exists.
- Permission constants are generated but not enforced — RBAC enforcement is expected to be a platform-level concern, wired in separately.
- Domain event publishing is a `# TODO` comment in each command handler — wire to your message bus (Kafka/Redpanda/etc.) once that integration exists.
- Alembic isn't initialized per module; `migrations/` contains only a placeholder file per entity as a reminder.

The CLI generates a module's own code completely and correctly — it deliberately does not reach into platform-level packages that don't exist yet in your specific backend.

## License

Proprietary — internal tool. Not published to public package indexes.