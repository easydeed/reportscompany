"""
The structural gate: did the migration actually happen?

WHY THIS FILE EXISTS, AND WHY NOTHING ELSE COULD DO ITS JOB
-----------------------------------------------------------
A restructure's premise is that output does not change. That makes **every
output-shaped assertion in this repository guaranteed to pass whether or not the
restructure happened** — the render diff, the contrast audit, the golden files
would all report success on a migration that had been entirely undone.

That is not hypothetical. Midway through this workstream a `git checkout` during
recovery from a bad edit discarded two completed migrations. Their block FILES
survived, so the repository briefly held two orphaned templates that nothing
rendered — and the whole suite was green, correctly, because the inline markup
they were meant to replace had come back with them. The green was accurate about
behaviour and silent about structure.

So these assertions are about the SHAPE of the code:

    every block file has a caller
    every caller names a block that exists
    no layout still assembles HTML where a block exists
    the counts agree with the map

Run against that orphaned state, `test_every_block_file_has_a_caller` fails and
names `masthead` and `signature` — which is the check being proved rather than
assumed, the same discipline as flipping the autoescape flag to watch the damage.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from email_fixtures import render  # noqa: E402
from worker.email.template import (  # noqa: E402
    CONDITIONAL_BLOCKS, INVARIANT_BLOCKS, LAYOUT_MAP, REPORT_BLOCKS,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "worker"
TEMPLATE = SRC / "email" / "template.py"
BLOCKS = SRC / "templates" / "email" / "blocks"

#: Every §06 block, plus the two this migration added. `chrome` and `grid` are
#: not in §06's list: they are what remained in Python once the named blocks
#: were extracted, and leaving them out would have meant the module still held
#: HTML while claiming otherwise.
EXPECTED_BLOCKS = {
    "masthead", "spec_list", "read", "table", "gallery", "bands", "cta", "signature",
    "chrome", "grid",
}

RENDER_CALL = re.compile(r'render_block\(\s*\n?\s*"([a-z_]+)"')


def source() -> str:
    return TEMPLATE.read_text()


def block_files() -> set:
    return {p.stem for p in BLOCKS.glob("*.jinja2")}


def called_blocks() -> set:
    return set(RENDER_CALL.findall(source()))


# ---------------------------------------------------------------------------
# Every file has a caller, every caller has a file
# ---------------------------------------------------------------------------

def test_every_block_file_has_a_caller():
    """
    THE ORPHAN CHECK. This is the one that would have caught the lost migration:
    a `.jinja2` sitting in the blocks directory that no code renders is a
    migration that did not land, and nothing about the output says so.
    """
    orphans = sorted(block_files() - called_blocks())
    assert not orphans, (
        f"block file(s) with no caller: {orphans}. Either the migration that "
        f"was supposed to use them was lost, or they are dead and should be "
        f"deleted. A template nothing renders is invisible to every other test "
        f"in this repository."
    )


def test_every_render_block_call_names_a_file_that_exists():
    """
    The other direction. Jinja raises `TemplateNotFound` at RENDER time, so a
    typo'd block name in a branch that only one report type reaches would ship
    and fail for that type alone.
    """
    missing = sorted(called_blocks() - block_files())
    assert not missing, f"render_block() names block(s) with no file: {missing}"


def test_the_block_set_is_what_the_consolidation_intended():
    assert block_files() == EXPECTED_BLOCKS, (
        f"blocks on disk: {sorted(block_files())}\n"
        f"expected:       {sorted(EXPECTED_BLOCKS)}\n"
        f"Adding a block is fine — update this set deliberately so the addition "
        f"is a decision rather than a drift."
    )


# ---------------------------------------------------------------------------
# No layout still assembles HTML where a block exists
# ---------------------------------------------------------------------------

def markup_bearing_functions() -> dict:
    """
    {function name: line count} for every function that still builds HTML in a
    Python string literal. Detected by an f-string or plain triple-quoted return
    or `+=` whose content contains a tag.
    """
    lines = source().split("\n")
    starts = [(i, m.group(1)) for i, l in enumerate(lines) if (m := re.match(r"^def (\w+)", l))]
    out = {}
    for (a, name), (b, _) in zip(starts, starts[1:] + [(len(lines), None)]):
        body = "\n".join(lines[a:b])
        if re.search(r"(return|\+=) f?'{3}|(return|\+=) f?\"{3}", body) and "<" in body:
            out[name] = b - a
    return out


#: Functions still holding HTML, with why. Empty is the goal; each entry is a
#: commitment to a reader that its presence is known rather than overlooked.
KNOWN_MARKUP_HOLDERS: dict = {}


def test_no_function_still_builds_html_in_python():
    """
    The migration's actual claim. `test_every_block_file_has_a_caller` proves the
    blocks are used; this proves nothing was left behind — a function can call a
    block for half its output and still concatenate the other half.
    """
    found = markup_bearing_functions()
    unexpected = {k: v for k, v in found.items() if k not in KNOWN_MARKUP_HOLDERS}
    assert not unexpected, (
        "function(s) still assembling HTML in Python:\n"
        + "\n".join(f"    {v:>4} lines  {k}" for k, v in sorted(unexpected.items(), key=lambda x: -x[1]))
        + "\n\nExtract the markup into a block, or add the function to "
          "KNOWN_MARKUP_HOLDERS with a reason."
    )


def test_the_known_holders_list_is_not_stale():
    """
    An exemption for a function that no longer exists, or no longer holds
    markup, is a lie that makes the list above look shorter than it is.
    """
    found = markup_bearing_functions()
    stale = sorted(k for k in KNOWN_MARKUP_HOLDERS if k not in found)
    assert not stale, f"KNOWN_MARKUP_HOLDERS names function(s) that no longer hold markup: {stale}"


# ---------------------------------------------------------------------------
# The declared per-layout sequence, checked against what actually renders
# ---------------------------------------------------------------------------

#: The key `render_block` kwarg that distinguishes one shape of a block from
#: another, per block. Without it `read` appears twice in a sequence with no way
#: to tell the insight callout from the Quick Take panel.
_VARIANT_KWARG = {
    "chrome": "piece", "read": "variant", "gallery": "size",
    "grid": "shape", "spec_list": "variant",
}


def observed_sequence(report_type, brand):
    """
    The blocks a real render actually emits, in first-use order, as
    `block:variant` — recorded by wrapping `render_block`, so this is behaviour
    and not a reading of the source.
    """
    from worker.email import template as tmpl
    seen = []
    original = tmpl.render_block

    def recording(name, **ctx):
        key = _VARIANT_KWARG.get(name)
        label = f"{name}:{ctx[key]}" if key and key in ctx else name
        if label not in seen:
            seen.append(label)
        return original(name, **ctx)

    tmpl.render_block = recording
    try:
        render(report_type, brand)
    finally:
        tmpl.render_block = original
    return seen


@pytest.mark.parametrize("report_type", sorted(REPORT_BLOCKS))
def test_the_declared_block_sequence_matches_what_renders(report_type):
    """
    THE MAP IS DATA AND THE DATA IS CHECKED.

    A table in a module docstring describing which blocks a layout uses is a
    comment: correct on the day it is written and unfalsifiable afterwards. This
    renders each report type, records every `render_block` call, and requires the
    result to equal `LAYOUT_BLOCKS[layout]` exactly — so the declaration cannot
    drift from the code, in either direction.
    """
    observed = [b for b in observed_sequence(report_type, "#0D9488")
                if b.split(":")[0] not in INVARIANT_BLOCKS]
    assert observed == list(REPORT_BLOCKS[report_type]), (
        f"{report_type} (layout '{LAYOUT_MAP[report_type]}')\n"
        f"  declared: {list(REPORT_BLOCKS[report_type])}\n"
        f"  rendered: {observed}"
    )


@pytest.mark.parametrize("report_type", sorted(LAYOUT_MAP))
def test_the_invariant_blocks_render_on_every_report_type(report_type):
    """
    §06: "masthead, agent block and footer invariant." A footer that renders on
    seven of eight report types is a CAN-SPAM failure on the eighth, and no
    per-layout test would notice.
    """
    observed = {b.split(":")[0] for b in observed_sequence(report_type, "#0D9488")}
    missing = [b for b in INVARIANT_BLOCKS if b not in observed]
    assert not missing, f"{report_type} did not render {missing}"


def test_every_report_type_has_a_declared_sequence():
    undeclared = sorted(set(LAYOUT_MAP) - set(REPORT_BLOCKS))
    assert not undeclared, f"report type(s) with no declared block sequence: {undeclared}"


@pytest.mark.parametrize("report_type", sorted(REPORT_BLOCKS))
def test_the_conditional_blocks_stay_conditional(report_type):
    """
    `filter_blurb`, `section_label` and `bands` are absent from every declared
    sequence because the standard fixture supplies no filter description and no
    band data. That absence is a property of the FIXTURE, so it has to be
    asserted — otherwise a refactor that started emitting them unconditionally
    would simply update the declarations and look intentional.
    """
    observed = set(observed_sequence(report_type, "#0D9488"))
    leaked = sorted(set(CONDITIONAL_BLOCKS) & observed)
    assert not leaked, (
        f"{report_type} rendered {leaked} from a fixture that supplies no data "
        f"for them — they are no longer conditional"
    )


def test_a_conditional_block_does_render_when_its_data_is_present():
    """
    The other half, and the one that stops the test above from passing on a
    block that has been deleted: given a filter description, the callout appears.
    """
    from email_fixtures import METRICS, LISTINGS, BASE_BRAND
    from worker.email.template import schedule_email_html
    import worker.email.template as tmpl
    seen = []
    original = tmpl.render_block
    tmpl.render_block = lambda name, **c: (seen.append(f"{name}:{c.get('piece', '')}"), original(name, **c))[1]
    try:
        schedule_email_html(
            account_name="X", report_type="market_snapshot", city="La Verne",
            zip_codes=None, lookback_days=30, metrics=METRICS,
            pdf_url="https://x.test/a.pdf",
            unsubscribe_url="https://x.test/u?token=" + "a" * 64,
            brand=dict(BASE_BRAND, primary_color="#0D9488"), listings=LISTINGS,
            filter_description="Under $1.5M", sender_type="REGULAR",
            total_found=50, total_shown=8,
        )
    finally:
        tmpl.render_block = original
    assert "chrome:filter_blurb" in seen, (
        "the filter callout did not render even with a filter_description — the "
        "block may be dead rather than conditional"
    )


def test_every_declared_block_exists_on_disk():
    named = {b.split(":")[0] for seq in REPORT_BLOCKS.values() for b in seq}
    named |= set(INVARIANT_BLOCKS)
    named |= {b.split(":")[0] for b in CONDITIONAL_BLOCKS}
    missing = sorted(named - block_files())
    assert not missing, f"the declarations name block(s) with no file: {missing}"


def test_every_block_file_appears_in_a_declaration():
    """
    The mirror. `test_every_block_file_has_a_caller` proves something calls each
    file; this proves the declarations account for each one, so a block used
    somewhere the map does not describe shows up rather than hiding behind a
    generic caller.
    """
    declared = {b.split(":")[0] for seq in REPORT_BLOCKS.values() for b in seq}
    declared |= set(INVARIANT_BLOCKS)
    declared |= {b.split(":")[0] for b in CONDITIONAL_BLOCKS}
    undeclared = sorted(block_files() - declared)
    assert not undeclared, f"block file(s) in no declaration: {undeclared}"


# ---------------------------------------------------------------------------
# The controls
# ---------------------------------------------------------------------------

def test_the_orphan_check_can_actually_fail(tmp_path, monkeypatch):
    """
    POSITIVE CONTROL, and the reason to trust the check above. Reproduces the
    exact state the lost migration left behind — a block file present and no
    caller — and asserts the check names it.
    """
    import test_block_structure as mod
    monkeypatch.setattr(mod, "block_files", lambda: {"masthead", "signature", "cta"})
    monkeypatch.setattr(mod, "called_blocks", lambda: {"cta"})
    with pytest.raises(AssertionError) as e:
        mod.test_every_block_file_has_a_caller()
    assert "masthead" in str(e.value) and "signature" in str(e.value)


def test_the_markup_check_can_actually_fail(monkeypatch):
    """NEGATIVE CONTROL for the other assertion."""
    import test_block_structure as mod
    monkeypatch.setattr(mod, "markup_bearing_functions", lambda: {"_build_thing": 42})
    with pytest.raises(AssertionError) as e:
        mod.test_no_function_still_builds_html_in_python()
    assert "_build_thing" in str(e.value)


def test_the_detector_finds_markup_in_a_known_shape():
    """
    The markup detector is a regex over source, so it can silently match nothing.
    This gives it a function it must find.
    """
    probe = 'def _x():\n    return f\'\'\'<table><tr><td>{v}</td></tr></table>\'\'\'\n'
    lines = probe.split("\n")
    assert re.search(r"(return|\+=) f?'{3}", probe) and "<" in probe, (
        "the pattern markup_bearing_functions() relies on no longer matches an "
        "obvious case; the empty result above would mean nothing"
    )
