# Security Policy

`zynkoh-cli` is a developer tool maintained by [Shiv Kumar](https://github.com/shivkumarsinghsky).
It runs locally or in CI and is not operated as a hosted service.

## Reporting a vulnerability

Please report security issues privately through GitHub's
[private vulnerability reporting](https://github.com/shivkumarsinghsky/zynkoh-cli/security/advisories/new)
rather than opening a public issue. Include the command you ran, the generated file and the
behaviour you observed.

## Scope

- The CLI itself (path handling, file writing, template rendering).
- **Generated code.** A template that produces insecure code (for example, a query that can
  skip the tenant filter, or a filter that accepts arbitrary column names) is a security issue
  in this repository, even though the vulnerable code lives in the generated module.

## Secrets

The CLI reads no credentials and the repository contains none. Generated modules read their
database URL and other settings from environment variables through `pydantic-settings`; never
commit a real `.env` file.
