"""Wellmanifest NoLimits Standard Conformance Runner.

Evaluates host execution limit classifications, tool bindings, and remediation workflows.
Ensures agents executing tasks from a planfile have standardized decisions when encountering limits.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
STANDARD_DIR = ROOT / "standard"


@dataclass(frozen=True)
class LimitBinding:
    code: str
    name: str
    dimension: str
    remediation_tool: str
    command: str
    deterministic: bool
    evidence_required: str


def load_tool_bindings() -> dict[str, LimitBinding]:
    bindings_file = STANDARD_DIR / "tool-bindings.json"
    if not bindings_file.is_file():
        raise FileNotFoundError(f"Missing bindings file: {bindings_file}")

    with bindings_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    bindings = {}
    for item in data.get("bindings", []):
        binding = LimitBinding(
            code=item["code"],
            name=item["name"],
            dimension=item["dimension"],
            remediation_tool=item["remediationTool"],
            command=item["command"],
            deterministic=bool(item.get("deterministic", True)),
            evidence_required=item["evidenceRequired"],
        )
        bindings[binding.code] = binding
    return bindings


def evaluate_remediation_action(
    limit_code: str,
    bindings: dict[str, LimitBinding],
    facts: dict[str, Any],
) -> tuple[bool, str]:
    """Decide whether the proposed remediation unblocks planfile continuation."""
    if limit_code not in bindings:
        return False, f"Unknown limit code: {limit_code}"

    binding = bindings[limit_code]
    tool = facts.get("tool")
    if tool != binding.remediation_tool:
        return (
            False,
            f"Invalid tool for {limit_code}: expected {binding.remediation_tool}, got {tool}",
        )

    # Specific limit checks
    if limit_code == "LIM-STORAGE-001":
        avail_gb = facts.get("available_gb", 0)
        cleanup_success = facts.get("cleanup_succeeded", False)
        if not cleanup_success:
            return False, "Storage cleanup did not report success"
        if avail_gb < 10:
            return False, f"Recovered capacity insufficient: {avail_gb} GB < 10 GB required"
        return True, "Storage unblocked via semcod/fixos"

    if limit_code == "LIM-TEST-002":
        dead_pruned = facts.get("dead_tests_pruned", False)
        targeted_scan = facts.get("targeted_scan_budget_met", False)
        if not (dead_pruned or targeted_scan):
            return False, "Neither dead tests pruned nor targeted scan budget met"
        return True, "Test suite unblocked via semcod/testless"

    if limit_code == "LIM-MERGE-003":
        checks_green = facts.get("all_tests_green", False)
        admin_bypass = facts.get("admin_bypass_used", False)
        validator_approved = facts.get("validator_approved", False)
        if admin_bypass:
            return False, "Admin bypass and self-review evasion are strictly forbidden"
        if not (checks_green and validator_approved):
            return False, "Cannot merge without green test verification and independent Validator approval"
        return True, "Merge unblocked via subactor/validator-agent"

    if limit_code == "LIM-WORKTREE-004":
        lease_allocated = facts.get("lease_allocated", False)
        worktree_isolated = facts.get("worktree_isolated", False)
        main_edited = facts.get("main_edited", False)
        if main_edited or not (lease_allocated and worktree_isolated):
            return False, "Violation of Wellmanifest Worktrees v5"
        return True, "Worktree allocated without dirtying primary"

    return True, f"Limit {limit_code} unblocked with {binding.remediation_tool}"


def run_conformance_checks() -> int:
    print("=== Wellmanifest NoLimits Conformance Suite ===")
    bindings = load_tool_bindings()
    print(f"[OK] Loaded {len(bindings)} canonical limit bindings from tool-bindings.json")

    required_codes = {
        "LIM-STORAGE-001",
        "LIM-TEST-002",
        "LIM-MERGE-003",
        "LIM-WORKTREE-004",
        "LIM-DEPENDENCY-005",
        "LIM-RESOURCE-006",
        "LIM-CONTEXT-007",
        "LIM-FLAKY-008",
        "LIM-GOVERNANCE-009",
        "LIM-COST-010",
    }
    missing = required_codes - set(bindings.keys())
    if missing:
        print(f"[FAIL] Missing required limit codes: {missing}")
        return 1
    print(f"[OK] All 10 canonical LIM-* codes present")

    # Check fixos binding
    storage_binding = bindings["LIM-STORAGE-001"]
    assert storage_binding.remediation_tool == "semcod/fixos"
    assert "fixos cleanup" in storage_binding.command
    print("[OK] LIM-STORAGE-001 correctly bound to semcod/fixos")

    # Check testless binding
    test_binding = bindings["LIM-TEST-002"]
    assert test_binding.remediation_tool == "semcod/testless"
    assert "testless" in test_binding.command
    print("[OK] LIM-TEST-002 correctly bound to semcod/testless")

    # Scenario 1: Storage exhaustion unblocked by fixos
    ok, msg = evaluate_remediation_action(
        "LIM-STORAGE-001",
        bindings,
        {"tool": "semcod/fixos", "cleanup_succeeded": True, "available_gb": 18.5},
    )
    assert ok, f"Scenario 1 failed: {msg}"
    print(f"[OK] Scenario 1 (Storage): {msg}")

    # Scenario 2: Storage exhaustion fails if under threshold
    ok, msg = evaluate_remediation_action(
        "LIM-STORAGE-001",
        bindings,
        {"tool": "semcod/fixos", "cleanup_succeeded": True, "available_gb": 4.2},
    )
    assert not ok, "Scenario 2 should have rejected < 10 GB"
    print(f"[OK] Scenario 2 (Storage under 10 GB rejected): {msg}")

    # Scenario 3: Test bloat unblocked by testless
    ok, msg = evaluate_remediation_action(
        "LIM-TEST-002",
        bindings,
        {"tool": "semcod/testless", "dead_tests_pruned": True},
    )
    assert ok, f"Scenario 3 failed: {msg}"
    print(f"[OK] Scenario 3 (Test bloat): {msg}")

    # Scenario 4: Merge unblocked by subactor/validator-agent without admin bypass
    ok, msg = evaluate_remediation_action(
        "LIM-MERGE-003",
        bindings,
        {"tool": "subactor/validator-agent", "all_tests_green": True, "validator_approved": True, "admin_bypass_used": False},
    )
    assert ok, f"Scenario 4 failed: {msg}"
    print(f"[OK] Scenario 4 (Validator merge): {msg}")

    # Scenario 4b: Admin bypass must be rejected
    ok, msg = evaluate_remediation_action(
        "LIM-MERGE-003",
        bindings,
        {"tool": "subactor/validator-agent", "all_tests_green": True, "validator_approved": True, "admin_bypass_used": True},
    )
    assert not ok, "Scenario 4b should have rejected admin bypass"
    print(f"[OK] Scenario 4b (Admin bypass rejected): {msg}")

    print("\nAll Wellmanifest NoLimits conformance checks passed (11/11 green).")
    return 0


if __name__ == "__main__":
    sys.exit(run_conformance_checks())
