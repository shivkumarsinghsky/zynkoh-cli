# ADR-001: Pure planning separated from rendering and writing

## Context
A generator decides which files to create and where. If that logic writes to disk as it goes,
`--dry-run` becomes a partial run, conflicts are discovered halfway through, and tests need a
real filesystem for every assertion.

## Decision
Each generator implements `plan_files()`, which returns `PlannedFile(template, output_path)`
entries and performs no I/O. `BaseGenerator.generate()` renders every planned file, queues the
results in a `FileWriter`, and only then executes the writes. `FileWriter` alone decides
whether a file is created, skipped as a conflict, overwritten (`--force`) or reported
(`--dry-run`).

## Alternatives
- **Write while planning:** simpler code, but no true preview and partial output on failure.
- **Generate into a temp directory, then move:** gives atomicity but complicates appends to existing files such as the module router.

## Trade-offs
Two passes over the plan, and appends (router includes, manifest updates) need their own
idempotent path (`plan_appends()` with a marker line).

## Consequences
Generator logic is unit-tested by asserting on the plan; `--dry-run` shows exactly what a real
run would write; existing files are never overwritten without `--force`.
