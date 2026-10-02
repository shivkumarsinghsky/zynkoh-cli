# ADR-003: Versioned template directories

## Context
Generated code is committed and then edited by developers. If a CLI upgrade changed what
`zynkoh create feature` produces, regenerating a resource in an older module would mix two
conventions in one module.

## Decision
Templates live under `templates/v1/`. Each module records `generator_template_version` in
`module.yaml`. A change that alters the shape of generated code goes into a new `v2/`
directory; `v1` receives only fixes that make its output correct (for example, a missing
import or a wrong column type).

## Alternatives
- **Single template set with feature flags:** flags multiply and old output cannot be reproduced.
- **Separate CLI releases per convention:** forces teams to manage several installed versions.

## Trade-offs
Duplicate templates when a `v2` is introduced.

## Consequences
Teams can pin a CLI release in CI (`@v1.1.0`) and upgrade conventions deliberately.
