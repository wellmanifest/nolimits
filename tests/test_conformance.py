import sys
from pathlib import Path

# Add repo root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "standard"))

from conformance import run_conformance_checks


def test_nolimits_conformance():
    exit_code = run_conformance_checks()
    assert exit_code == 0
