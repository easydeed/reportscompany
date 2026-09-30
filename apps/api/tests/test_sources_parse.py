"""
D-147 — `apps/api` did not import on the Python version the repo pins for its
release check.

`services/email.py` had `\\u2019` inside the expression part of an f-string.
That is a syntax error before 3.12 and legal from 3.12 on. `backend-tests.yml`
runs on 3.12 and was green; `release-check.yml` pins 3.11 and would have died
on `from api.main import app` before reaching a single assertion — but it is
`workflow_dispatch` only, so nobody had run it. The whole API test suite was
uncollectable on the interpreter the pre-release gate uses, and the gate that
would have said so is the one that never runs.

One compile pass over every source file costs milliseconds and does not care
which of the two versions is right. It fails on whichever interpreter is
running, which is the only one whose opinion matters at that moment.

It is `compile()` and not an import on purpose: importing every module would
need every dependency installed and would execute module-level code. This
answers a narrower question — does the file parse here — which is exactly the
question that went unasked.
"""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]

#: Trees whose files ship or run. Not `node_modules`, not `.venv`, not
#: generated output.
ROOTS = ["apps/api/src", "apps/worker/src", "scripts", "tools"]


def _sources(root: Path):
    for p in sorted(root.rglob("*.py")):
        if any(part in {"node_modules", ".venv", "__pycache__", "build", "dist"}
               for part in p.parts):
            continue
        yield p


@pytest.mark.parametrize("root", ROOTS)
def test_every_source_file_parses_on_this_interpreter(root):
    broken = []
    for path in _sources(REPO / root):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            broken.append(f"{path.relative_to(REPO)}:{exc.lineno}: {exc.msg}")
    assert not broken, (
        "source files that do not parse on this Python "
        f"({'.'.join(map(str, __import__('sys').version_info[:2]))}):\n  "
        + "\n  ".join(broken)
    )
