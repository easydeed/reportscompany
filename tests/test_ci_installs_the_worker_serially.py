"""CI installs the worker's dependencies one package at a time (D-357).

`backend-tests.yml` installs the API lock and then the worker lock into one
shared venv. The worker lock pins older versions of packages the API lock
installed, so the second install downgrades them; Poetry's default parallel
installer ran those swaps concurrently, and on #266 one `pip uninstall` read
site-packages while another removed a dist-info. pip crashed before any test
ran. `POETRY_INSTALLER_PARALLEL=false` on that step runs the swaps in turn.

Red on main: the worker install step sets no such variable.
"""
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/backend-tests.yml"


def _steps():
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    return [s for job in jobs.values() for s in job.get("steps", [])]


def test_the_worker_install_is_serial():
    installs = [s for s in _steps()
                if s.get("working-directory") == "apps/worker" and "poetry install" in str(s.get("run", ""))]
    assert len(installs) == 1, f"expected one worker `poetry install` step, found {len(installs)}"
    env = installs[0].get("env") or {}
    assert str(env.get("POETRY_INSTALLER_PARALLEL")).lower() == "false", (
        "the worker install downgrades packages in the shared venv; it must run serially (D-357)")


def test_the_worker_install_still_follows_the_api_install_into_one_venv():
    """The serial setting matters only because of this order; if the order or
    the shared venv goes, re-read D-357 rather than keep the setting blindly."""
    steps = _steps()
    order = [s.get("working-directory") for s in steps if "poetry install" in str(s.get("run", ""))]
    assert order == ["apps/api", "apps/worker"], order
    venvs = {(s.get("env") or {}).get("VIRTUAL_ENV") for s in steps if "poetry install" in str(s.get("run", ""))}
    assert len(venvs) == 1, venvs
