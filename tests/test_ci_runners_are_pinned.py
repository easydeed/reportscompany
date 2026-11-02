"""Every workflow job runs on a named Ubuntu release, not `ubuntu-latest`.

On or before 2026-11-02 `ubuntu-latest` moved to 26.04, where the pinned
Playwright cannot install Chromium (`Playwright does not support chromium on
ubuntu26.04-x64`). Backend Tests died in that setup step on every run, main
included, before a single test executed — a red that said nothing about the
code. A runner image is a dependency; it changes when we choose, like the rest.
"""
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github/workflows"


def test_no_job_runs_on_a_moving_image():
    moving = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for name, job in (yaml.safe_load(path.read_text(encoding="utf-8")).get("jobs") or {}).items():
            runner = str(job.get("runs-on", ""))
            if runner.endswith("-latest"):
                moving.append(f"{path.name}:{name} runs on {runner}")
    assert not moving, moving
