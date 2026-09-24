#!/usr/bin/env python3
"""
Regenerate apps/worker/tests/golden/email_facts/*.json — the render-diff gate for
Workstream C's template consolidation.

The consolidation replaces Python f-strings with one Jinja2 template. Every
design decision was made already, in the colour work and in D-099, so the
restructure must change nothing a recipient sees — but it WILL change the bytes.
These files record what each document means rather than how it is spelled: the
text runs, their resolved foreground and background, the links, the images, the
custom properties, the classes and the element counts.

Run this ONLY to establish a new baseline deliberately. Running it to make a
failing diff pass discards the entire point of the gate.
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "apps/worker/tests"))

import os  # noqa: E402
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
import logging  # noqa: E402
logging.disable(logging.CRITICAL)

from _render_facts import facts, save  # noqa: E402
from email_fixtures import CASES, render  # noqa: E402

OUT = REPO / "apps/worker/tests/golden/email_facts"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, brand, report_type in CASES:
        save(OUT / f"{name}.json", facts(render(report_type, brand)))
    print(f"wrote {len(CASES)} fact files to {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
