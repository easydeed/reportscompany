"""An edit to the defect board runs the tests that read it (D-348).

`test_defect_list_counts.py` and `test_xfail_defect_links.py` read
`docs/DEFECT_LIST.md`. Until #261 neither of `backend-tests.yml`'s path filters
listed the board, so a board-only PR ran nothing that checks it.
"""
from pathlib import Path

import yaml
from scripts.release_gate import classify_paths

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/backend-tests.yml"


def test_board_changes_require_backend_tests():
    on = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))[True]  # YAML reads `on:` as True
    assert "workflow_call" in on
    assert classify_paths(["docs/DEFECT_LIST.md"])["backend"] is True
