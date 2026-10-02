# Contributing to zynkoh-cli

Thanks for your interest in `zynkoh-cli`. Bug reports, template fixes and new field types are welcome.

## Workflow

1. Fork and clone, then set up the environment:
   ```bash
   uv venv && source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```
2. Open an issue first for anything beyond a small fix (new field types, new generators, changes to default output) so the approach can be agreed before you invest time.
3. Branch as `feature/<short-description>` or `fix/<short-description>`.
4. Before opening a pull request, all of these must pass:
   ```bash
   pytest            # includes the end-to-end test that generates and runs a module
   ruff check .
   mypy src
   ```
5. Commit messages are short, imperative and scoped, for example `crud: add datetime filter support`.
6. The pull request description states what changed, why, and how you verified the generated output.

## Verifying template changes

Unit tests assert on the planned file list. Rendered-output correctness is covered by
`tests/integration/test_generated_module.py`, which generates a module, lints it, runs its
tests and calls its API. When you change a template, extend that test if the behaviour is new.
For exploratory checks you can also generate into a scratch directory:

```bash
cd "$(mktemp -d)"
zynkoh create module scratch
zynkoh create crud widget --module scratch --fields "name:str,price:decimal"
cd apps/modules/scratch && uv venv && uv pip install -e ".[dev]" && pytest && ruff check .
```

## Coding conventions

- Python 3.12+, full type hints, `from __future__ import annotations` at the top of every module.
- `commands/*.py` stay thin: parse → validate → build a `GenerationContext` → call a generator → report the result. No generation logic here.
- `generators/*.py` implement `plan_files()` (pure, no I/O) and optionally `plan_extra_files()` / `plan_appends()` for non-template-rendered or additive output (see `base_generator.py` for the contract).
- Validation errors raise `ModuleValidationError` or `FieldValidationError` with a clear, actionable message — never a bare `ValueError` or an unguarded exception that surfaces as a raw traceback to the CLI user.
- Never introduce a way for generated code to build SQL from unvalidated input — any new filter/sort/query capability must validate against an explicit, generated allowlist, matching the existing pattern in `templates/v1/crud/query_list.py.j2`.
- Run `ruff check .` before committing; the config in `pyproject.toml` is the source of truth for style (line length, import order, etc.) — don't fight it with inline `# noqa` unless there's a genuinely good reason, and explain that reason in a comment.

## Adding a new field type

To add a new `--fields` type (e.g. `email` as a distinct validated type):

1. Add it to `ALLOWED_FIELD_TYPES` in `validators/field_validator.py`.
2. Add its Python type mapping to the inline dict in every template that maps field types (`domain_entity.py.j2`, `command_create.py.j2`, `command_update.py.j2`, `schema_request.py.j2`, `schema_response.py.j2`, `persistence_model.py.j2`, and the filter-parameter map in `crud/router.py.j2` — search for `"decimal":` across `templates/` to find them all). `persistence_model.py.j2` also needs the SQLAlchemy column type.
3. Add a test case to `tests/unit/test_field_validator.py`.
4. Add the type to the field lists in `tests/integration/test_generated_module.py` so the end-to-end test covers it.

## Adding a new generator command (e.g. a future `zynkoh create worker`)

1. Add templates under `templates/v1/<name>/`.
2. Create `generators/<name>_generator.py` subclassing `BaseGenerator`, implementing `plan_files()` at minimum.
3. Create `commands/<name>.py` following the exact shape of `commands/entity.py` (validation → context → generator → result reporting → interactive prompt fallback).
4. Register it in `commands/create.py`.
5. Add planning-logic tests following `tests/unit/test_module_generator.py`'s pattern.
6. Update the README's [Commands](README.md#commands) table and [What gets generated](README.md#what-gets-generated) section.

## Code of conduct

Be respectful and constructive. Assume good intent, and keep discussion focused on the work.
