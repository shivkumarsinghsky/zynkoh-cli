# ADR-005: Unit of work owned by the request dependency

## Context
A command handler may change several aggregates. If each repository committed on its own, a
failure halfway through would leave partial state.

## Decision
Generated repositories only call `flush()`, never `commit()`. The request-scoped `get_db()`
dependency owns the transaction: it commits after the handler returns and rolls back on any
exception. The generated stub documents this contract in its docstring, and the end-to-end
tests use exactly that pattern.

## Alternatives
- **Commit in the repository:** simple, but breaks atomicity across repositories.
- **Explicit unit-of-work object passed to handlers:** more ceremony for the common single-aggregate case.

## Trade-offs
Background jobs and scripts that reuse repositories must manage their own transaction.

## Consequences
Handlers stay transaction-agnostic. Forgetting to commit in `get_db()` shows up immediately
in development, because created records are not returned by the next request.
