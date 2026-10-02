# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-02

### Fixed
- Generated modules failed to start: the module `pyproject.toml` now depends on `sqlalchemy[asyncio]`, which provides `greenlet`.
- `json` fields produced a persistence model that crashed on import; they now map to a `JSON` column.
- `decimal` fields were stored as floating point; they now use `Numeric(18, 4)` and `Decimal`.
- `date` fields were stored as timestamps; they now use a `Date` column.
- Soft-deleted rows were still returned by `get` and `list`; reads now exclude them.
- Updating or deleting a missing entity returned HTTP 500; it now returns 404.
- Repository `update` did not check the row's tenant; it now does.
- CRUD list filters for `date`, `datetime` and `decimal` were typed as strings; they now use proper types, and `json` columns are no longer offered as filter or sort fields.
- Commands for entities with a `datetime` field were missing the `datetime` import.
- Generated unit tests assumed soft delete and passed `None` for required date fields.
- The generated module `Dockerfile` installed the package before copying its code; it now copies `app/` first and runs as a non-root user.
- `--no-tenant-aware` on `feature` and `crud` generated code that could not run; it is now rejected with a clear error (ADR-002).

### Added
- End-to-end test suite that generates a module, lints it, runs its tests and exercises its API against a database.
- Post-generation formatting with Ruff, and a `[tool.ruff]` section in generated modules, so generated code is lint-clean.
- The `get_db()` stub documents the commit/rollback contract.
- Architecture documentation, six ADRs, CI and security workflows, a Docker image for the CLI.
- MIT license.

### Changed
- Strict `mypy` now passes for the CLI source.

## [1.0.0] - 2026-09-20

### Added
- `zynkoh create module`, `entity`, `feature` and `crud` generators with `--dry-run`, `--force` and interactive prompts.
- Versioned Jinja2 templates (`v1`), naming engine, field and module validators, module manifest (`module.yaml`).

[1.1.0]: https://github.com/shivkumarsinghsky/zynkoh-cli/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/shivkumarsinghsky/zynkoh-cli/releases/tag/v1.0.0
