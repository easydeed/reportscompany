"""Every key the market builder reads is a key something produces.

WHY THIS EXISTS (D-113)
-----------------------
`MarketReportBuilder._build_monthly_trend` reads `report_data["closed_history"]`
and returns `(None, None, None)` when it is absent. It is absent on every
production render, because no report builder emits it and `tasks.py` never adds
it — so §7.3's twelve-month trend chart has never appeared in a customer's
report, and D-102's page-1 decision that depends on it is unrealised.

**Nothing failed.** The chart's own tests supply `closed_history` themselves,
which is right for a unit test and means they prove the chart draws correctly
from data it is handed while saying nothing about whether it is ever handed
any. `measure_market_pagination.py` supplies it too, so even the pagination
measurements were taken in a state production does not reach.

THE SHAPE OF THE GAP, WHICH IS THE POINT
-----------------------------------------
A reader with a graceful fallback and no producer is invisible from both ends:
the reader looks careful, the producer's absence looks like nothing at all, and
every test that touches the feature hands it the input. The only way to see it
is to compare the two sets — which is what this does.

It is a CONTRACT test, not a data test: it asks which keys are read and which
are written, by parsing, and says nothing about their values.
"""
import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "apps/worker/src/worker"

#: Keys the builder reads that no producer is expected to write, with the
#: reason. An entry here is a claim that the fallback is the intended path.
#: Everything else must have a producer.
OPTIONAL = {
    "accent_color": "set by tasks.py from the theme, not by a report builder",
    "branding": "set by tasks.py from the affiliate row",
    "report_type": "set by tasks.py after the builder returns",
    "ai_insights": "set by tasks.py from the narrative generator, and the "
                   "report is complete without it",
    "agent_name": "read out of `branding`, not out of report_data's top level",
    "company_name": "as agent_name",
}


def _reads(path: Path, holder: str) -> set:
    """Keys read as `<holder>.get("k")` anywhere in `path`."""
    out = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and holder in ast.unparse(node.func.value)):
            out.add(node.args[0].value)
    return out


def _written(paths) -> set:
    """Every string key any dict literal or subscript assignment sets.

    Deliberately GENEROUS — a key written anywhere in the producing modules
    counts. A narrower rule would need to know which builder runs for which
    report type, and a test that overstates what is produced fails safe: it
    reports fewer gaps, never invents one.
    """
    out = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key in node.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        out.add(key.value)
            elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                if isinstance(node.slice.value, str):
                    out.add(node.slice.value)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "update":
                for arg in node.args:
                    if isinstance(arg, ast.Dict):
                        for key in arg.keys:
                            if isinstance(key, ast.Constant):
                                out.add(key.value)
    return out


PRODUCERS = [SRC / "report_builders.py", SRC / "tasks.py"]


def test_every_key_the_market_builder_reads_is_produced_somewhere():
    """
    THE GATE. A read with no producer is a feature that cannot run, and a
    graceful fallback makes it silent.

    If this fails, either wire the producer or add the key to `OPTIONAL` with
    the reason the fallback is the intended path. Do not delete the finding,
    and do not add a key here to clear a missing fetch — an exemption would
    say the feature is meant never to run, which is what D-113 was.

    Was `xfail(strict=True)` while D-113 stood. The marker came off with the
    fetch, which is what strict is for.
    """
    read = _reads(SRC / "market_builder.py", "report_data")
    produced = _written(PRODUCERS)
    orphans = sorted(k for k in read - produced if k not in OPTIONAL)
    assert orphans == [], (
        "the market builder reads these and nothing writes them, so the code "
        f"behind them never runs: {orphans}"
    )


def test_the_optional_list_does_not_outlive_what_it_excused():
    """An entry for a key nobody reads any more is one nobody rechecks."""
    read = _reads(SRC / "market_builder.py", "report_data")
    stale = sorted(set(OPTIONAL) - read)
    assert stale == [], f"OPTIONAL names keys the builder no longer reads: {stale}"


def test_the_reader_and_producer_sets_are_not_empty():
    """
    Zero orphans and zero reads look identical from outside — the same
    confusion that left the contrast auditor covering nothing.
    """
    assert len(_reads(SRC / "market_builder.py", "report_data")) >= 12
    assert len(_written(PRODUCERS)) >= 50


def test_the_gate_sees_a_planted_orphan(tmp_path):
    """
    A gate nobody has watched fail is a gate nobody has tested. This plants
    the exact shape of D-113 — a read with a graceful fallback — and checks it
    is reported.
    """
    fake = tmp_path / "builder.py"
    fake.write_text(
        "class B:\n"
        "    def go(self):\n"
        "        history = self.report_data.get('a_key_nothing_writes')\n"
        "        if not history:\n"
        "            return None\n"
        "        return history\n")
    read = _reads(fake, "report_data")
    assert "a_key_nothing_writes" in read
    assert "a_key_nothing_writes" not in _written(PRODUCERS)
