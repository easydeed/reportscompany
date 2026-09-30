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


def _read_groups(path: Path, holder: str) -> list:
    """Keys read off `holder`, grouped by alias chain.

    `comp.get("distance_miles") or comp.get("distance")` is ONE requirement
    with two spellings, not two requirements. Treating them separately makes
    the gate cry wolf on every alias in the codebase — and a gate that reports
    things that are fine gets its output skimmed, which is how a real finding
    gets missed.

    So an `or` chain of `.get()` calls on the same holder becomes one group,
    satisfied if ANY member is produced.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))

    def key_of(node):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and holder in ast.unparse(node.func.value)):
            return node.args[0].value
        return None

    groups, claimed = [], set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            keys = {k for v in node.values if (k := key_of(v))}
            if len(keys) > 1:
                groups.append(frozenset(keys))
                claimed |= keys
    for node in ast.walk(tree):
        if (k := key_of(node)) and k not in claimed:
            groups.append(frozenset({k}))
    # de-duplicate while keeping single-key groups that an alias group covers
    out, seen = [], set()
    for g in groups:
        if g not in seen:
            seen.add(g)
            out.append(g)
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


# ══════════════════════════════════════════════════════════════════════════
# THE GATE, GENERALISED — every consumer, not just the one D-113 was found in
# ══════════════════════════════════════════════════════════════════════════
#
# The test above was scoped to `market_builder.py` reading `report_data`,
# because that is where the first instance was found. Two more turned up
# elsewhere within the week — `estimated_value` (D-118) and `last_sale_*`
# (D-133) — both outside its reach. Jerry, 2026-09-30: extend it, and report
# what it catches, because a fourth makes this a structural property of the
# codebase rather than a recurring defect.
#
# It is a fourth and a great deal more. The baseline below is the measurement.
#
# WHY A BASELINE AND NOT AN xfail. A strict xfail per surface says "these are
# broken" and hides a NEW orphan appearing beside them. An exact baseline
# fails in both directions: a new gap is a failure, and a fixed gap is a
# failure too, because a stale baseline is how a ratchet stops ratcheting.

API = ROOT / "apps/api/src/api"


def _pydantic_model_keys(path: Path, class_name: str) -> set:
    """Field names declared on a pydantic model, read from source.

    Used for SiteX, where the authoritative producer is not a dict literal
    anywhere — the route does `sitex_data = property_data.model_dump()`, so
    the key set IS the model's fields and nothing else. Reading the class
    rather than the route is what makes this exact: the generous `_written`
    scan over `routes/property.py` reported 358 keys and hid the gap
    completely.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {n.target.id for n in node.body
                    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
    raise AssertionError(f"{class_name} not found in {path}")


#: (label, consumer, holder, producer-key-set callable, known orphans).
#: Each known-orphan set was verified by hand against the producer before
#: being written down; see docs/DEFECT_LIST.md D-135.
SURFACES = [
    (
        "property_builder reads sitex_data",
        SRC / "property_builder.py", "sitex_data",
        lambda: _pydantic_model_keys(API / "services/sitex.py", "PropertyData"),
        {
            # Read by _build_property_context / _build_stats_context, produced
            # by neither SiteX's model nor the wizard's payload. D-135.
            "pool", "zoning", "garage", "fireplace", "stories", "census_tract",
            "housing_tract", "lot_number", "page_grid", "partial_bath",
            "percent_improved", "tax_status", "tax_rate_area", "total_rooms",
            "num_units", "use_code", "mailing_address", "notes",
            "estimated_value",
            # Two nested blobs SiteX has never returned, whose defaults are
            # INVENTED figures — `female_ratio "51.5"`, `avg_beds "3"`,
            # `area_min_radius "0.1 mi"`. No live template renders either
            # context today, so nothing false is printed; wiring one up would
            # ship fabricated demographics. D-136.
            "neighborhood", "area_analysis",
            # Read as `latitude or lat`; only the long spelling is produced,
            # and the group covers it — listed because the short alias is dead.
            # (Grouping means these never reach the orphan list; kept here as
            # documentation would rot, so they are asserted absent below.)
        },
    ),
    (
        "mobile_reports reads property_data",
        API / "routes/mobile_reports.py", "property_data",
        # `lead_pages.py` writes this blob too. Leaving it out reported `apn`
        # and `property_type` as orphans when both are written at
        # lead_pages.py:302,312 — a gate that names an incomplete producer set
        # INVENTS gaps, which is the failure mode that gets a gate ignored.
        lambda: _written([SRC / "tasks.py", API / "routes/lead_pages.py"]),
        {"last_sale_date", "last_sale_price", "tax_assessed_value"},  # D-133
    ),
]


def _orphans(consumer: Path, holder: str, produced: set, optional=frozenset()) -> set:
    """Alias groups where no spelling is produced. Returns the group's keys."""
    out = set()
    for group in _read_groups(consumer, holder):
        if group & produced or group & set(optional):
            continue
        out |= group
    return out


@pytest.mark.parametrize("label,consumer,holder,producer,known", SURFACES,
                         ids=[s[0] for s in SURFACES])
def test_the_orphan_set_for_each_surface_is_exactly_what_was_measured(
        label, consumer, holder, producer, known):
    """Both directions. A NEW orphan is a new feature that cannot run; a
    DISAPPEARED one means the baseline is stale and stopped protecting."""
    found = _orphans(consumer, holder, producer())
    new = sorted(found - known)
    fixed = sorted(known - found)
    assert not new, (
        f"{label}: these are read and nothing writes them, so the code behind "
        f"them never runs: {new}. Wire the producer, or add to the baseline "
        f"with the reason."
    )
    assert not fixed, (
        f"{label}: {fixed} no longer orphaned — remove from the baseline so it "
        f"keeps failing on a regression. A stale baseline protects nothing."
    )


def test_the_generalised_gate_is_actually_reaching_the_code():
    """Zero orphans and zero reads look identical from outside."""
    for label, consumer, holder, producer, _ in SURFACES:
        assert len(_read_groups(consumer, holder)) >= 10, f"{label} reads almost nothing"
        assert len(producer()) >= 10, f"{label} producer set is suspiciously small"


def test_an_alias_chain_counts_as_satisfied_by_either_spelling():
    """`a.get("x") or a.get("y")` is one requirement with two spellings.

    Without this the gate reports every alias in the codebase as an orphan,
    and output nobody trusts is output nobody reads.
    """
    groups = _read_groups(SRC / "property_builder.py", "sitex_data")
    lat = [g for g in groups if "lat" in g]
    assert lat and lat[0] == frozenset({"latitude", "lat"}), (
        f"expected latitude/lat to group; got {lat}"
    )
    assert not _orphans(SRC / "property_builder.py", "sitex_data", {"latitude"}) & {"lat"}


def test_the_generalised_gate_sees_a_planted_orphan(tmp_path):
    """A gate nobody has watched fail is a gate nobody has tested.

    Plants D-118's exact shape — a read whose `or` fallback is the only path —
    and checks the grouping does not swallow it. This is the case the alias
    rule could plausibly get wrong: `x or y` where NEITHER is produced must
    still be reported, and `x or CONSTANT` is not an alias chain at all.
    """
    fake = tmp_path / "consumer.py"
    fake.write_text(
        "def build(self):\n"
        "    sitex_data = self.d\n"
        "    a = sitex_data.get('nothing_writes_this') or sitex_data.get('nor_this')\n"
        "    b = sitex_data.get('lonely_orphan')\n"
        "    c = sitex_data.get('is_produced') or 0\n"
        "    return a, b, c\n")
    found = _orphans(fake, "sitex_data", {"is_produced"})
    assert found == {"nothing_writes_this", "nor_this", "lonely_orphan"}, found


def test_a_naming_mismatch_is_reported_not_excused():
    """D-133's third instance is not 'nobody writes it' — it is 'the writer
    calls it something else'. `mobile_reports` reads `tax_assessed_value`;
    `tasks.py` writes `assessed_value`. The gate must not treat a near-miss
    as a match, because that is the one a reader's eye skips over."""
    produced = _written([SRC / "tasks.py", API / "routes/lead_pages.py"])
    assert "assessed_value" in produced
    assert "tax_assessed_value" not in produced
