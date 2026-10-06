"""
The branding preview's sample data, against what the builder actually reads.

WHAT THIS EXISTS TO PREVENT
---------------------------
`routes/branding_tools._render_sample_html` renders the real
`MarketReportBuilder` against `services/sample_report_data.get_sample_data` —
so a customer judging their logo and colours is looking at a document built
from a fixture. A key the builder reads and the fixture does not supply is a
section missing from that preview and present in the report their recipients
get, with nothing anywhere saying so.

Nobody had compared the two. `closed_history` is absent from all eight sample
report types, and it is what `_build_monthly_trend` needs: `market_snapshot`
and `inventory` are the two types that draw a trend chart, and both render
**~2,750 characters shorter** in the preview than with the key supplied.
D-173.

WHY THE COMPARISON IS DERIVED AND NOT A LIST
--------------------------------------------
A list of expected keys is a third copy of the contract, and this project has
spent four defects on second copies (D-139, D-140, D-167, and the mirrored
metric functions). `scripts/derive_sample_vs_builder.py` reads the builder's
AST for keys taken directly off `report_data` and compares them against what
`get_sample_data` returns, per type.

`report_data` must be the DIRECT receiver. `(self.report_data.get("branding")
or {}).get("agent_name")` is a `.get` whose chain contains `report_data`, and
the inner key belongs to `branding` — counting it attributed `agent_name` and
`company_name` to the top level and produced two false positives out of seven,
in a script written to find a divergence.
"""
import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DERIVE = REPO / "scripts/derive_sample_vs_builder.py"

#: Keys the production path supplies and the preview path does not, with what
#: each one costs the preview. **This is a ratchet, not an allowance**: an
#: entry here is a known hole with a measurement attached, and a key that
#: appears and is NOT here fails the build.
KNOWN_PREVIEW_HOLES = {
    "closed_history":
        "the monthly trend chart. market_snapshot and inventory render ~2,750 "
        "chars shorter without it (D-173)",
    "closed_history_truncated":
        "the flag that refuses a median over a truncated fetch (D-078). "
        "Absent means 'not truncated', which is true of a fixture",
    "price_bands_note":
        "the caveat under the price-bands chart",
}


@pytest.fixture(scope="module")
def derived():
    spec = importlib.util.spec_from_file_location("_derive_sample", DERIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = module.main()
    assert rc == 0
    return json.loads(buf.getvalue())


def test_no_new_key_is_read_by_the_builder_and_supplied_by_nothing(derived):
    """THE RATCHET. A fourth hole fails the build.

    The three below are recorded with what they cost. A new one means the
    builder learned to read something the preview path has no producer for,
    and the preview silently lost a section — which is the whole of D-173.
    """
    missing = set(derived["read_but_supplied_by_nothing"])
    new = sorted(missing - set(KNOWN_PREVIEW_HOLES))
    assert not new, (
        f"the builder reads {new} and nothing on the branding-preview path "
        f"supplies it. Either supply it in `get_sample_data` or add it to "
        f"KNOWN_PREVIEW_HOLES with what its absence costs the preview — a "
        f"hole with a measurement is a decision, a hole without one is a "
        f"section nobody knows is missing."
    )


def test_the_recorded_holes_are_still_holes(derived):
    """The other half, and the half that usually rots.

    A fixed hole left in the list above is an allowance nobody rechecks, which
    is what `ALLOWED` in `test_absent_is_not_a_default` went wrong by.
    """
    missing = set(derived["read_but_supplied_by_nothing"])
    fixed = sorted(set(KNOWN_PREVIEW_HOLES) - missing)
    assert not fixed, (
        f"{fixed} is now supplied on the preview path. Remove it from "
        f"KNOWN_PREVIEW_HOLES — progress, and the list has to shrink to "
        f"record it."
    )


def test_the_read_set_is_not_empty(derived):
    """A derived set that comes back empty makes both tests above pass.

    §0.6: a derived set is only as complete as the input it was derived from,
    and this one is an AST walk over a file that could be moved or renamed.
    """
    assert len(derived["builder_reads"]) > 10, (
        f"the AST walk found only {derived['builder_reads']} keys read off "
        f"report_data — the scan is broken, not the builder simple"
    )


def test_no_sample_key_is_read_by_nothing_at_all(derived):
    """The reverse direction: sample data with no consumer.

    Three keys — `filters_label`, `period_label`, `report_date` — are returned
    by `get_sample_data` and appear in neither the builder nor any market
    template. They are the write-with-no-consumer family (D-009, D-113,
    D-133, D-135, D-164) in a fixture, which is the harmless end of it: they
    cost a reader working out whether a preview field is missing or was never
    wired.

    Recorded rather than deleted, because deleting a key from a fixture that
    three other callers may read is its own change.
    """
    dead = set(derived["supplied_read_by_nothing_at_all"])
    expected = {"filters_label", "period_label", "report_date"}
    assert dead == expected, (
        f"sample keys read by nothing changed: {sorted(dead)}, recorded as "
        f"{sorted(expected)}. A NEW one is a field somebody added to the "
        f"fixture and never wired; one GONE is progress and this set should "
        f"shrink."
    )
