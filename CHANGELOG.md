# Changelog

All notable changes to the `wellmanifest/nolimits` standard will be documented in this file.

## [0.1.0] - 2026-09-27

### Added
- Canonical Wellmanifest NoLimits Standard (`wellmanifest/nolimits@v1`).
- Catalog of 10 Host Execution Limits (`LIM-*`) spanning storage, testing, git, environment, and resources.
- Machine-readable `standard/tool-bindings.json` binding each limit to the designated `semcod/*` remediation tool (`semcod/fixos`, `semcod/testless`, `semcod/pactfix`, etc.).
- Machine-readable `standard/nolimits.schema.json` for standardized limit reporting.
- Env DSL decision equations in `standard/limits-rules.env`.
- Executable conformance test suite `standard/conformance.py` passing 10/10 green.
- Practical examples for storage exhaustion (`LIM-STORAGE-001`) and test suite bloat (`LIM-TEST-002`).
