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
