"""
D-152 — the CI table in SOURCE_OF_TRUTH.md described coverage that did not exist.

Four rows, and every one was wrong in the same direction. `release-check.yml`
and `e2e.yml` were listed as "PR + push" when one was `workflow_dispatch`-only
and dead (D-151) and the other has been manual since D-045. The two real ones
said "PR + push" flat, which reads as *every* PR, when both are path-filtered.

**That bare phrase is what made the dead rows plausible.** If the working
workflows claim to run on every PR, a workflow that does nothing claiming the
same is unremarkable. The cost of `release-check.yml` was never the wasted
minutes; it was a table that made someone believe four things were checked.

Correcting the prose is the diligence fix, and the note added there asks the
next person to keep the path lists in step. This is the structural one. It
does not check wording — that would be brittle and would get deleted — it
checks two properties that cannot be satisfied by an out-of-date table:

  1. every workflow has a row, and every row names a real workflow;
  2. every path in a workflow's filter appears in its row, so a filter that
     gains or loses a directory shows up here.

THE SECOND ASSERTION IS D-089'S RULE, AND IT CAUGHT A LIVE ONE. A workflow
that runs on `pull_request` must list its own file in BOTH filters, or it can
be edited, reviewed and merged without ever running. `frontend-tests.yml`
listed itself under `push` and not `pull_request`; `backend-tests.yml` had
listed itself in both since D-089 and was the model. Both are fixed, and this
keeps the third one honest.
"""
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / ".github/workflows"
DOC = REPO / "docs/architecture/SOURCE_OF_TRUTH.md"


def _triggers(path: Path) -> dict:
    """A workflow's `on:` block.

    `yaml.safe_load` reads the bare key `on` as the BOOLEAN True — it is a
    YAML 1.1 truthy token — so `d["on"]` is a KeyError on every GitHub
    workflow ever written. Look under both.
    """
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    return d.get(True) or d.get("on") or {}


def _workflow_files():
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def _ci_table() -> dict:
    """{filename: row text} from the CI table in §2.7."""
    rows = {}
    for line in DOC.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("|"):
            continue
        m = re.search(r"`([\w.-]+\.ya?ml)`", line)
        if m:
            rows[m.group(1)] = line
    return rows


def test_every_workflow_has_a_row_and_every_row_a_workflow():
    listed = set(_ci_table())
    present = {p.name for p in _workflow_files()}
    assert listed == present, (
        f"the CI table in {DOC.relative_to(REPO)} §2.7 disagrees with "
        f".github/workflows/:\n"
        f"  in the table, not on disk: {sorted(listed - present) or 'none'}\n"
        f"  on disk, not in the table: {sorted(present - listed) or 'none'}\n"
        f"A row for a workflow that does not exist is how release-check.yml "
        f"read as coverage for months after it stopped being able to run."
    )


@pytest.mark.parametrize("wf", _workflow_files(), ids=lambda p: p.name)
def test_the_row_names_every_path_the_filter_carries(wf):
    row = _ci_table().get(wf.name)
    assert row, f"{wf.name} has no row (covered by the test above)"

    paths = set()
    for event, cfg in _triggers(wf).items():
        if isinstance(cfg, dict):
            paths.update(cfg.get("paths") or [])
    if not paths:
        return  # manual-only, or unfiltered; nothing to keep in step

    missing = [p for p in sorted(paths) if p.strip('"').rstrip("/*").rstrip("/")
               not in row and p.strip('"') not in row
               and not (p.endswith(".yml") and "its own file" in row)]
    assert not missing, (
        f"{wf.name}'s row does not mention {missing}. The table says what this "
        f"workflow covers, and a reader plans around it — a filter the row "
        f"omits is coverage somebody thinks they have."
    )

    # AND THE OTHER DIRECTION, which the first version of this test did not
    # check — found the hard way: a stray `git checkout` reverted the
    # `tools/**` addition to backend-tests.yml while the row still advertised
    # it, and all seven tests stayed green. A row promising a path the filter
    # does not carry is the exact failure this file exists for, pointing the
    # other way.
    claimed = set(re.findall(r"`([\w./-]+(?:/\*\*|\.\w+))`", row))
    # The row's first column names the workflow itself, in backticks, and the
    # path list may name it again with its directory. Neither is a claim about
    # coverage.
    claimed -= {wf.name, f".github/workflows/{wf.name}"}
    stale = sorted(c for c in claimed if c not in {p.strip('"') for p in paths})
    assert not stale, (
        f"{wf.name}'s row claims {stale}, which its filter does not carry. The "
        f"row promises coverage the workflow will not deliver."
    )


@pytest.mark.parametrize("wf", _workflow_files(), ids=lambda p: p.name)
def test_a_pr_triggered_workflow_lists_its_own_file(wf):
    """D-089: a job you can edit without triggering the job.

    Only applies where BOTH triggers are path-filtered. A workflow with no
    filter already runs on everything.
    """
    on = _triggers(wf)
    pr = on.get("pull_request")
    if not isinstance(pr, dict) or not pr.get("paths"):
        return

    rel = f".github/workflows/{wf.name}"
    for event in ("push", "pull_request"):
        cfg = on.get(event)
        if not isinstance(cfg, dict) or not cfg.get("paths"):
            continue
        assert rel in cfg["paths"], (
            f"{wf.name} filters `{event}` by path but does not list itself, so "
            f"a change to this workflow does not run it. frontend-tests.yml "
            f"had exactly this gap on `pull_request` (D-152)."
        )
