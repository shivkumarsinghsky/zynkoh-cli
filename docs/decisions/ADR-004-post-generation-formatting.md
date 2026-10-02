# ADR-004: Post-generation formatting with Ruff

## Context
Generated modules ship with `ruff` in their dev dependencies, so their output should pass it.
Import blocks in templates depend on the field types an entity uses (`date`, `Decimal`, `Any`
appear or not), so keeping imports sorted inside Jinja requires fragile conditional ordering.
Before this decision a typical generated module had around 45 lint findings.

## Decision
After writing, `BaseGenerator.generate()` runs `ruff check --fix --select I,UP,F401` over the
Python files it created, overwrote or appended to. The generated `pyproject.toml` carries its
own `[tool.ruff]` configuration (including FastAPI's `Depends`/`Query` as immutable calls), and
Ruff resolves that configuration from each file's location. Ruff is a runtime dependency of
the CLI. Formatting is best-effort: if it cannot run, generation still succeeds because the
files are already valid Python.

## Alternatives
- **Hand-order imports in every template:** brittle across field-type combinations.
- **Run `ruff format` as well:** rewrites more than needed and can fight team formatting choices.

## Trade-offs
One extra subprocess per generation and a dependency on Ruff.

## Consequences
Generated code is lint-clean on the first run; the end-to-end test enforces it.
