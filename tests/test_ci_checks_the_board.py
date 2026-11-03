"""An edit to the defect board runs the tests that read it (D-348).

`test_defect_list_counts.py` and `test_xfail_defect_links.py` read
`docs/DEFECT_LIST.md`. Until #261 neither of `backend-tests.yml`'s path filters
listed the board, so a board-only PR ran nothing that checks it.
"""
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/backend-tests.yml"


def test_both_filters_list_the_board():
    on = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))[True]  # YAML reads `on:` as True
    for event in ("push", "pull_request"):
        assert "docs/DEFECT_LIST.md" in on[event]["paths"], event
