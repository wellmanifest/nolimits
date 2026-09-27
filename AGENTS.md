# AGENTS.md — Wellmanifest NoLimits Standard

This repository defines the canonical rules for host limit classification and remediation.
When executing planfile tickets across any repository under `/home/tom/github`:

## General Rules
1. Never stall or exit an autonomous sprint when encountering known resource or environment limits.
2. Consult `standard/tool-bindings.json` for the canonical remediation action.
3. For storage deficits (< 10 GB), execute `fixos cleanup --threshold-gb 10` via `semcod/fixos`.
4. For test bloat, use `semcod/testless` to eliminate dead tests and scope verification runs.
5. For blocked PR merges with passing tests, use `wellmanifest/merge@ticket-008` auto-merge.
6. For dirty primary checkouts, strictly allocate isolated worktrees under Wellmanifest Worktrees v5.

## Conformance Verification
Always verify conformance with:
```bash
python3 standard/conformance.py
```
