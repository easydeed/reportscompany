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

`report_data` must be the receiver. `(self.report_data.get("branding")
or {}).get("agent_name")` is a `.get` whose chain contains `report_data`, and
the inner key belongs to `branding` — counting it attributed `agent_name` and
`company_name` to the top level and produced two false positives out of seven,
in a script written to find a divergence.

AND THE FIX FOR THOSE FALSE POSITIVES BOUGHT A FALSE NEGATIVE
-------------------------------------------------------------
Narrowing the rule to a DIRECT receiver made `market_builder.py:452` invisible:
`_build_header_context` does `data = self.report_data` at 435 and then reads
`data.get("filters_label", "")` as the masthead subtitle. The first version of
this file therefore pinned `filters_label` as read by nothing, and the version
that shipped asserted it. It is read, by the builder, on every market report.

Reads are now followed through local aliases, and
`test_the_alias_rule_still_finds_the_aliased_read` fails if that stops
working — because the direct-receiver rule passed every other test in this
file while being wrong.

THE SCOPE OF THE REVERSE CHECK IS PART OF ITS CLAIM
---------------------------------------------------
The reverse half scanned the market Jinja tree and published the result as
`read_by_nothing_at_all`. `period_label` and `report_date` are read seven
times in `apps/web/lib/templates.ts` — the legacy print/social surface, whose
own docstring says *"NOT DEAD CODE — do not delete… Two archived documents
asserted this route had been removed. Both were wrong."*

A one-surface scan published as a repo-wide verdict is D-131, which was cited
three times as a reason to delete something live. The surfaces are now
enumerated, each is asserted to match files, and the assertion below is about
those surfaces by name rather than about "anything".
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


def test_every_supplied_key_has_a_named_consumer(derived):
    """The reverse direction: sample data with no consumer, scoped honestly.

    `period_label` and `report_date` are returned by `get_sample_data` and
    read by neither the builder nor the market templates. They are NOT
    unconsumed: `apps/web/lib/templates.ts` reads both, seven times, with a
    fallback, for the legacy print and social surfaces.

    So this does not assert that a key is read by "nothing". It asserts that
    every key the fixture supplies is read by at least one ENUMERATED surface,
    and the derivation reports which. A key with no surface is either newly
    orphaned or a surface this list has not been told about, and the message
    says so, because getting that distinction wrong is how D-131 happened.
    """
    read_by = derived["supplied_not_read_by_builder_read_by"]
    orphans = derived["supplied_read_by_no_enumerated_surface"]
    assert not orphans, (
        f"{orphans} is supplied by `get_sample_data` and read by none of "
        f"{derived['consumer_surfaces']}. Before calling it dead: is there a "
        f"surface missing from CONSUMER_SURFACES in "
        f"scripts/derive_sample_vs_builder.py? `apps/web/lib/templates.ts` "
        f"was missing once, and two live keys were filed as unconsumed."
    )
    # The non-empty guard (§0.6): a derivation that found no consumers for
    # anything would pass the assertion above by measuring nothing.
    assert read_by, (
        "no key is supplied-but-not-read-by-the-builder, so this test "
        "measured nothing. That is possible — but check the derivation before "
        "believing it."
    )
    for key, where in read_by.items():
        assert where, f"{key} reached the loop with no surface"


def test_the_alias_rule_still_finds_the_aliased_read(derived):
    """`filters_label` is the regression that shipped green.

    A read off a local alias of `report_data` is invisible to a
    direct-receiver scan, and every other test in this file passed while the
    scan was wrong. So the alias path is asserted by name: if the rule is
    narrowed again, this fails instead of the finding quietly reversing.
    """
    # THE UNFILTERED SET, because this is a question about the SCANNER.
    #
    # This read `builder_reads_via_alias`, which is filtered to keys a
    # direct-receiver scan would MISS. On 2026-10-10 `filters_label` gained a
    # second, direct read in `_v2_gallery`'s empty state — so it left that set,
    # and by then every key in the aliased block was also read directly, so the
    # set was empty and this test failed claiming the alias rule had been
    # narrowed. It had not: the rule still found the aliased site, and the key
    # had simply stopped being the witness.
    #
    # A gate scoped to one key, meaning the rule — §0.6's
    # instance-named-as-class, in a gate about scanning. Scoped to the rule now
    # and asserted two ways, so neither a narrowed rule nor a vanished alias
    # can pass quietly.
    via_all = derived["builder_reads_via_alias_all"]
    assert via_all, (
        "the alias rule found NO aliased reads anywhere in market_builder.py. "
        "Either every `data = self.report_data` alias is gone — fine, and this "
        "test should be retired with them — or the rule was narrowed and a "
        "whole class of reads is invisible again, which is how `filters_label` "
        "shipped green."
    )
    assert "filters_label" in via_all, (
        f"`filters_label` is no longer found through an alias: "
        f"{sorted(via_all)}. It is read off `data` in `_build_header_context`, "
        f"and that read is the one the direct-receiver scan missed."
    )
    assert "filters_label" in derived["builder_reads"]


def test_the_consumer_surfaces_all_exist(derived):
    """An empty surface shrinks the read set silently.

    `surface_text()` raises on a glob that matches nothing, so reaching here
    with a surface list at all means each one matched. Asserted anyway,
    because the failure mode is a scan that gets quieter rather than louder.
    """
    assert len(derived["consumer_surfaces"]) >= 3, (
        f"only {derived['consumer_surfaces']} surfaces enumerated. A surface "
        f"dropped from the list turns its keys into deletion candidates."
    )


# ─────────────────────────────────────────────────────────────────────────────
# The cap relationship, derived rather than restated.
#
# `sample_report_data.py` carried a seven-row table of `PDF_CONFIG` caps in its
# docstring. Five of seven figures were stale, `open_houses` was absent, and
# the "+ K more" callout the table was written around had been removed from
# every type. Nothing caught it because a docstring has no reader that fails.
#
# WHY A DERIVED RELATIONSHIP AND NOT A SNAPSHOT OF THE NUMBERS. A pinned
# `{type: cap}` dict is the fourth copy of PDF_CONFIG and would need updating
# on the next builder change — and whoever updated it would update it to match,
# which is how the table got stale in the first place. What is pinned instead
# is the only thing the fixture is claiming: WHICH types it supplies more
# listings than the builder will render. That is a decision about the sample
# document, so a change to it should need a decision.
# ─────────────────────────────────────────────────────────────────────────────

#: Types where the fixture deliberately supplies more listings than the cap,
#: so the sample PDF's "a curated sample of N" copy has a real number under it.
#: Everything else is under its cap and renders in full — which is correct, not
#: a gap: the catalog types were moved to cap=200 and `more_template = None` on
#: purpose (`market_builder.py:153`).
EXERCISES_TRUNCATION = {"market_snapshot"}


@pytest.fixture(scope="module")
def caps():
    sys.path.insert(0, str(REPO / "apps/worker/src"))
    sys.path.insert(0, str(REPO / "apps/api/src"))
    from api.services.sample_report_data import (  # noqa: E402
        SUPPORTED_SAMPLE_REPORT_TYPES, get_sample_data,
    )
    from worker.market_builder import PDF_CONFIG  # noqa: E402

    out = {}
    for rt in SUPPORTED_SAMPLE_REPORT_TYPES:
        data = get_sample_data(rt, city="Irvine", lookback_days=30)
        listings = data.get("listings") or data.get("listings_sample") or []
        out[rt] = (len(listings), PDF_CONFIG[rt]["cap"])
    return out


def test_the_fixture_exercises_truncation_on_exactly_the_recorded_types(caps):
    """The relationship, derived from PDF_CONFIG on both sides."""
    over = {rt for rt, (n, cap) in caps.items() if n > cap}
    assert over == EXERCISES_TRUNCATION, (
        f"the fixture now exceeds the builder's cap on {sorted(over)}, "
        f"recorded as {sorted(EXERCISES_TRUNCATION)}. Measured: "
        f"{ {rt: f'{n} listings vs cap {cap}' for rt, (n, cap) in sorted(caps.items())} }. "
        f"A type that STOPPED exceeding its cap no longer exercises the "
        f"'curated sample of N' copy in the sample PDF; a new one does. "
        f"Either is a change to what a customer approves their branding "
        f"against, so decide it rather than re-pinning it."
    )


def test_every_sample_type_supplies_listings(caps):
    """The non-empty guard: a fixture that supplies none would pass above."""
    empty = sorted(rt for rt, (n, _) in caps.items() if n == 0)
    assert not empty, f"{empty} supply no listings, so their caps mean nothing"


def test_no_cap_figure_is_restated_beside_the_fixture():
    """The anti-copy gate.

    `cap=N` in this module's source is a fifth copy of a number
    `market_builder.PDF_CONFIG` owns. The prose above may DESCRIBE the stale
    figures as history — that is the record of the defect — but a live
    `cap=<n>` is the defect coming back.
    """
    import re
    src = (REPO / "apps/api/src/api/services/sample_report_data.py").read_text(
        encoding="utf-8")
    restated = re.findall(r"cap\s*=\s*\d+", src)
    assert not restated, (
        f"{restated} restates a PDF_CONFIG cap in sample_report_data.py. "
        f"Read it from `market_builder.PDF_CONFIG` instead — the seven-row "
        f"table that used to live in that docstring went stale in five rows "
        f"and nothing noticed, because a docstring has no reader that fails."
    )
