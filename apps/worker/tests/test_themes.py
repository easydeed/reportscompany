"""
Workstream A — the token layer (`worker.themes`).

WHAT IS BEING GUARDED
---------------------
One affiliate colour in, five derived values out. The values reach every PDF,
every email and every social card, so the interesting failures are not "it
raised" — they are "it returned a plausible colour that nobody can read", which
is precisely what ships today:

    Luxury Estates renders its price in #0D9488 at 3.74:1 on white.

THE SHAPE OF THE TESTS
----------------------
A contrast property is easy to satisfy dishonestly. `primary_ink = "#000000"`
passes "ink clears 4.5:1 on white" for every input in the universe, and a
5,000-case property test would celebrate it. So the property tests come paired
with guards that a degenerate implementation fails: the ink keeps the colour's
hue, it is left alone when it already passes, and distinct inputs stay distinct.
That pairing is the lesson from D-095's suite, where a constant key function
passed the headline assertion.

The golden file is the other half. A property test says "no output is illegal";
the golden file says "these six outputs are exactly these". Only the second one
notices when a change is legal and still wrong for the six affiliates who have
it today.
"""
from __future__ import annotations

import colorsys
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.themes import (  # noqa: E402
    AA_NORMAL,
    DARK_SURFACE,
    NEAR_BLACK,
    TOKENS,
    WHITE,
    contrast,
    derive_theme,
    normalize_hex,
    relative_luminance,
)

GOLDEN = Path(__file__).resolve().parent / "golden" / "themes.json"

#: The measured floor for `contrast(on_primary, primary)`. NOT a design choice
#: — it is what a binary white/near-black pick can reach, derived below and
#: measured at 4.27. See D-097.
ON_PRIMARY_ACHIEVABLE = 4.25

#: Fixed seed. A property test that picks different colours each run reports a
#: different failure each run, which is indistinguishable from flake and gets
#: re-run instead of read. The seed is part of the evidence.
SEED = 20260923
SAMPLE = 5000


def random_hexes(n=SAMPLE, seed=SEED):
    rng = random.Random(seed)
    return ["#%06x" % rng.randrange(0x1000000) for _ in range(n)]


def hue_of(value: str) -> float:
    v = normalize_hex(value)[1:]
    r, g, b = (int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)[0] * 360.0


def hue_gap(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def chroma_of(value: str) -> int:
    v = normalize_hex(value)[1:]
    r, g, b = (int(v[i:i + 2], 16) for i in (0, 2, 4))
    return max(r, g, b) - min(r, g, b)


# ---------------------------------------------------------------------------
# The instrument itself. Everything below depends on contrast() being right,
# so it is checked against values that can be verified by hand before it is
# used to judge anything.
# ---------------------------------------------------------------------------

def test_contrast_agrees_with_known_values():
    assert round(contrast("#000000", "#ffffff"), 1) == 21.0
    assert round(contrast("#ffffff", "#ffffff"), 1) == 1.0
    assert round(contrast("#777777", "#ffffff"), 2) == 4.48
    # symmetric — the ratio does not care which is foreground
    assert contrast("#0d9488", "#ffffff") == contrast("#ffffff", "#0d9488")


def test_contrast_reproduces_the_master_plans_measured_table():
    """
    §02 of the master plan states six measurements taken independently of this
    code. Reproducing them is what makes every number below trustworthy — and
    it is the check that would have caught a luminance formula off by the sRGB
    linearisation step, which is the usual way this goes wrong and which still
    produces plausible-looking ratios.
    """
    measured = {
        "#DC2626": 4.83,
        "#0D9488": 3.74,
        "#0E7490": 5.36,
        "#F59E0B": 2.15,
        "#84CC16": 1.98,
        "#7C3AED": 5.70,
    }
    for hexv, expected in measured.items():
        assert round(contrast(hexv, WHITE), 2) == expected, (
            f"{hexv} measures {contrast(hexv, WHITE):.2f}:1 here but the master "
            f"plan states {expected}:1 — one of the two is wrong and the whole "
            f"workstream rests on which"
        )


def test_the_luminance_here_agrees_with_the_one_already_live():
    """
    `property_builder._relative_luminance` is used on every render today. Two
    implementations of the same standard in one repo is a divergence waiting to
    happen; this is the tripwire. If it fires, the fix is to delete one of them,
    not to loosen the tolerance.
    """
    from worker.property_builder import _hex_to_rgb, _relative_luminance

    for hexv in ("#dc2626", "#0d9488", "#ffffff", "#000000", "#84cc16", "#14151a"):
        r, g, b = _hex_to_rgb(hexv)
        assert _relative_luminance(r, g, b) == pytest.approx(
            relative_luminance(hexv), abs=1e-12
        ), f"the two luminance implementations disagree on {hexv}"


# ---------------------------------------------------------------------------
# §4.2 — property test over 5,000 random hex values
# ---------------------------------------------------------------------------

def test_ink_clears_aa_on_white_for_5000_random_colours():
    """
    The headline property, and the one Workstream A exists to establish.
    """
    bad = []
    for hexv in random_hexes():
        ink = derive_theme(hexv)["primary_ink"]
        ratio = contrast(ink, WHITE)
        if ratio < AA_NORMAL:
            bad.append((hexv, ink, round(ratio, 3)))
    assert not bad, (
        f"{len(bad)} of {SAMPLE} colours produced an ink below {AA_NORMAL}:1 on "
        f"white; first five: {bad[:5]}"
    )


def test_the_ink_property_is_not_satisfied_by_going_black():
    """
    THE GUARD ON THE PROPERTY ABOVE. `primary_ink = "#000000"` passes it for
    every input. This is what distinguishes a derivation from a constant.

    Two claims:
      - the ink keeps the hue it came from, so it still reads as the brand
      - the ink is no darker than it has to be: one step lighter fails AA

    HUE TOLERANCE, MEASURED. Scaling all three channels by one factor preserves
    hue exactly in real arithmetic; the drift is entirely 8-bit rounding, twelve
    times over, and it is inversely proportional to chroma. Over 20,000 random
    colours:

        chroma  32- 63   max drift 5.42°
        chroma  64- 95   max drift 2.67°
        chroma  96-255   max drift 2.03°
        chroma   0- 31   max drift  150°   <- a near-grey has no hue to keep

    So the check applies above chroma 64 with 3° of room. The excluded band is
    not a blind spot being hidden: at chroma under 32 the "hue" of the input is
    itself rounding noise, and asserting anything about it would be asserting
    the noise.
    """
    from worker.themes import _MAX_STEPS, _STEP, _scale

    off_hue, overshot = [], []
    for hexv in random_hexes(800):
        if chroma_of(hexv) < 64:
            continue
        ink = derive_theme(hexv)["primary_ink"]
        if hue_gap(hue_of(ink), hue_of(hexv)) > 3.0:
            off_hue.append((hexv, ink))
        if ink != normalize_hex(hexv):
            # Replay the sequence forward rather than dividing by 0.94 to get
            # the previous value. Rounding is not invertible: for #e76a36 the
            # real previous step is #c0582d at 4.49:1 but the inverse gives
            # #bf582d at 4.52:1, which lands on the other side of the threshold
            # and accuses the code of overshooting when it did not.
            #
            # BOUNDED. The first run of this test against a deliberately broken
            # `_ink` (one that returns #000000 for everything) did not fail — it
            # HUNG, because scaling an integer channel by 0.94 rounds 1 back to
            # 1 and the sequence never reaches black. A test that hangs under a
            # regression is worse than one that misses it: it reads as a stuck
            # CI job rather than as a result.
            prev, cur = None, normalize_hex(hexv)
            for _ in range(_MAX_STEPS + 1):
                if cur == ink:
                    break
                prev, cur = cur, _scale(cur, _STEP)
            else:
                pytest.fail(
                    f"{hexv}: ink {ink} is not on the 6% darkening sequence at "
                    f"all, so it was not produced by the specified derivation"
                )
            if prev is not None and contrast(prev, WHITE) >= AA_NORMAL:
                overshot.append((hexv, ink, prev))
    assert not off_hue, f"ink lost the source hue for {off_hue[:5]}"
    assert not overshot, (
        f"ink is darker than the rule requires for {overshot[:5]} — one 6% step "
        f"lighter would still have cleared AA, so the loop is not stopping at "
        f"the first passing value"
    )


#: §0.6's two-way link: the marker names its defect, and D-098's entry lists the
#: test. Strict, so the day `on_primary` learns to adjust the fill the build
#: says so instead of staying quietly yellow.
_D098_GATED = pytest.mark.xfail(
    strict=True,
    reason="D-098 — a white/near-black binary cannot reach 4.5:1 against every "
           "fill; the ceiling is 4.27:1 at L=0.196 and ~5% of sRGB sits under it",
)


@_D098_GATED
def test_on_primary_clears_aa_against_the_fill_for_5000_random_colours():
    """
    §4.2 asks for this property. The derivation §3.1 specifies cannot provide
    it, and that is a finding about the spec rather than a bug in the code:

        on_primary picks the better of #ffffff and #14151a. Those two are fixed,
        so the worst case is the fill whose luminance sits exactly between them
        — L = 0.196, where both options score 4.27:1.

    Measured: 1056 of 20000 random colours (5.3%) land under 4.5:1.

    Left as a strict xfail rather than relaxed to 4.27, because relaxing it in
    silence is how a spec quietly becomes whatever the code happens to do. The
    live assertion is the next test; the decision is Jerry's and is recorded on
    D-097.
    """
    bad = []
    for hexv in random_hexes():
        t = derive_theme(hexv)
        if contrast(t["on_primary"], t["primary"]) < AA_NORMAL:
            bad.append(hexv)
    assert not bad, f"{len(bad)} of {SAMPLE} fills cannot carry readable text"


def test_on_primary_always_reaches_the_achievable_ceiling():
    """
    What the specified derivation DOES guarantee. Asserted so that a future
    change which makes `on_primary` worse is caught, even while the 4.5 target
    above is unreachable.
    """
    bad = []
    for hexv in random_hexes():
        t = derive_theme(hexv)
        ratio = contrast(t["on_primary"], t["primary"])
        if ratio < ON_PRIMARY_ACHIEVABLE:
            bad.append((hexv, round(ratio, 3)))
    assert not bad, (
        f"{len(bad)} colours fell below the measured floor of "
        f"{ON_PRIMARY_ACHIEVABLE}:1: {bad[:5]}"
    )


def test_on_primary_picks_the_better_of_the_two_candidates():
    """
    GUARD. "Always return #ffffff" passes the ceiling test for most colours.
    This asserts the choice is actually a choice.
    """
    seen = set()
    for hexv in random_hexes(2000):
        t = derive_theme(hexv)
        assert t["on_primary"] in (WHITE, NEAR_BLACK)
        best = max((contrast(c, t["primary"]), c) for c in (WHITE, NEAR_BLACK))[1]
        assert t["on_primary"] == best, (
            f"{hexv}: chose {t['on_primary']} but {best} scores higher"
        )
        seen.add(t["on_primary"])
    assert seen == {WHITE, NEAR_BLACK}, (
        f"only ever returned {seen} across 2000 colours — the other branch is dead"
    )


def test_every_theme_has_all_six_tokens_and_they_are_valid_colours():
    for hexv in random_hexes(1000):
        t = derive_theme(hexv)
        assert tuple(t) == TOKENS, f"key set drifted: {tuple(t)}"
        for k, v in t.items():
            assert normalize_hex(v) == v, f"{k}={v!r} is not a normalised #rrggbb"


# ---------------------------------------------------------------------------
# primary_on_dark — the sixth token
# ---------------------------------------------------------------------------

def test_on_dark_clears_aa_on_the_fixed_surface_for_5000_random_colours():
    """
    The guarantee. Reachable for every input, unlike `on_primary`, because the
    VALUE moves — brightening ends at white, and white on #0f172a is 17.85:1.
    """
    bad = [(h, round(contrast(derive_theme(h)["primary_on_dark"], DARK_SURFACE), 3))
           for h in random_hexes()
           if contrast(derive_theme(h)["primary_on_dark"], DARK_SURFACE) < AA_NORMAL]
    assert not bad, f"{len(bad)} of {SAMPLE} failed; first five: {bad[:5]}"


def test_on_dark_is_not_satisfied_by_going_white():
    """
    THE GUARD. `primary_on_dark = "#ffffff"` passes the test above for every
    input. Two claims: a brand that already clears the bar is untouched, and one
    that does not keeps its hue on the way up.
    """
    # Amber and lime are already far past 4.5 on this surface
    for hexv in ("#F59E0B", "#84CC16", "#0D9488"):
        assert derive_theme(hexv)["primary_on_dark"] == normalize_hex(hexv), (
            f"{hexv} already clears the bar and was brightened anyway"
        )
    off = []
    for hexv in random_hexes(600):
        if chroma_of(hexv) < 64:
            continue
        got = derive_theme(hexv)["primary_on_dark"]
        if got == WHITE:
            continue  # legitimately ran out of headroom
        if hue_gap(hue_of(got), hue_of(hexv)) > 4.0:
            off.append((hexv, got))
    assert not off, f"brightening lost the brand's hue: {off[:5]}"


def test_on_dark_spends_saturation_last():
    """
    D-099 established this by measurement on the PDF path: reducing saturation
    on every brightening step turns a dark brand into a grey. The token layer
    uses the same rule, so the two derivations cannot drift apart on it.
    """
    from worker.themes import _brighten
    got = derive_theme("#1B365D")["primary_on_dark"]
    assert contrast(got, DARK_SURFACE) >= AA_NORMAL
    assert chroma_of(got) > 100, f"{got} has chroma {chroma_of(got)} — washed out"
    # and one step raises value before touching saturation
    import colorsys as cs
    v0 = cs.rgb_to_hsv(0x1B / 255, 0x36 / 255, 0x5D / 255)
    nxt = normalize_hex(_brighten("#1B365D"))[1:]
    v1 = cs.rgb_to_hsv(*(int(nxt[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    assert v1[2] > v0[2] and v1[1] >= v0[1] - 0.01


def test_the_guarantee_is_against_the_fixed_surface_and_no_other():
    """
    **THE CONDITION ON JERRY'S DECISION, PINNED SO IT CANNOT BE FORGOTTEN.**

    One fixed neutral means the token is true on that neutral. Six of the eight
    dark surfaces the templates paint today are LIGHTER than #0f172a, so a value
    that clears 4.5:1 here does not clear it there — 3.06:1 on classic's
    #1B365D. That is the migration the decision implies, not a defect in the
    token, and this test states the gap rather than asserting it away.

    When the dark panels have migrated, the loop below should find nothing and
    the test becomes the stronger claim. Until then it documents the checklist.
    """
    STILL_PAINTED = ("#0b0f1a", "#0f1629", "#111827", "#1a1a1a",
                     "#0f1a45", "#18235c", "#15216e", "#1b365d")
    token = derive_theme("#0D9488")["primary_on_dark"]
    assert contrast(token, DARK_SURFACE) >= AA_NORMAL, "the guarantee itself"

    short = {s: round(contrast(token, s), 2)
             for s in STILL_PAINTED if contrast(token, s) < AA_NORMAL}
    # Measured 2026-09-23. Asserted exactly: if a panel migrates to the neutral
    # this fails and the entry gets updated, which is the point.
    assert short == {"#0f1a45": 4.47, "#18235c": 3.91,
                     "#15216e": 3.80, "#1b365d": 3.24}, (
        f"the set of surfaces where the token does not hold has changed: {short}"
    )


# ---------------------------------------------------------------------------
# §4.2 — degenerate inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hexv", ["#FFFFFF", "#000000", "#FFFF00"])
def test_degenerate_inputs_return_usable_values(hexv):
    """
    The three the spec names. "Usable" is the operative word: the loop must not
    run to the floor and hand back black for everything, which would technically
    satisfy every contrast assertion in this file.
    """
    t = derive_theme(hexv)
    assert tuple(t) == TOKENS
    assert contrast(t["primary_ink"], WHITE) >= AA_NORMAL
    assert contrast(t["on_primary"], t["primary"]) >= ON_PRIMARY_ACHIEVABLE


def test_white_does_not_become_black():
    """
    #FFFFFF has nowhere to go but down, and 12 steps of 6% is the whole journey
    to AA. It should stop on arrival at a mid grey, not continue to the floor.
    """
    t = derive_theme("#FFFFFF")
    assert t["primary_ink"] == "#727272"
    assert contrast(t["primary_ink"], WHITE) == pytest.approx(4.81, abs=0.01)
    assert t["on_primary"] == NEAR_BLACK
    assert t["tint"] == "#ffffff"


def test_black_is_left_exactly_where_it_is():
    """
    Already 21:1. The loop must exit on the first check having darkened nothing
    — and with integer channels at zero, a 6% step cannot change it, so without
    that first check this is the input that spins.
    """
    t = derive_theme("#000000")
    assert t["primary_ink"] == "#000000"
    assert t["primary_dark"] == "#000000"
    assert t["on_primary"] == WHITE
    assert t["tint"] == "#f0f0f0", "6% black over white"


def test_pure_yellow_stays_yellow():
    """
    The slowest chromatic case: 1.07:1 on white, twelve steps to clear AA. The
    result must still be a yellow — #797900, a dark olive — and not an
    unrecognisable near-black. This is the concrete form of "rather than looping
    to the floor".
    """
    t = derive_theme("#FFFF00")
    assert t["primary_ink"] == "#797900"
    assert hue_gap(hue_of(t["primary_ink"]), 60.0) < 1.0, "no longer yellow"
    assert chroma_of(t["primary_ink"]) > 100, "washed out to a grey"
    assert contrast(t["primary_ink"], WHITE) >= AA_NORMAL


def test_the_step_bound_is_never_reached():
    """
    `_ink` has a 64-step bound so a rounding stall cannot become an infinite
    loop. If any real colour needed it, the bound would be silently deciding the
    output. Measured: the worst case is 12.
    """
    from worker.themes import _MAX_STEPS, _STEP, _scale

    worst = 0
    for hexv in random_hexes(3000) + ["#ffffff", "#ffff00", "#00ffff", "#ffe4b5"]:
        cur, steps = normalize_hex(hexv), 0
        while contrast(cur, WHITE) < AA_NORMAL and steps < _MAX_STEPS:
            cur = _scale(cur, _STEP)
            steps += 1
        worst = max(worst, steps)
    assert worst < _MAX_STEPS, "the bound is load-bearing, not a safety net"
    assert worst <= 13, f"worst case moved to {worst} steps — was 12"


# ---------------------------------------------------------------------------
# §4.2 — determinism, and caching per affiliate
# ---------------------------------------------------------------------------

def test_same_input_same_output_in_one_process():
    for hexv in random_hexes(500):
        assert derive_theme(hexv) == derive_theme(hexv.upper())


def test_determinism_across_processes():
    """
    A fresh interpreter, because that is the real deployment shape: a Celery
    prefork child derives the tokens for a PDF, a different worker derives them
    for the email that links to it, and they must agree or the two halves of one
    send are different colours.

    Run as a subprocess rather than trusted from the same process — anything
    seeded at import, or any dict whose order leaks into the result, only shows
    up here.
    """
    src = Path(__file__).resolve().parents[1] / "src"
    prog = (
        "import sys, json; sys.path.insert(0, %r);"
        "from worker.themes import derive_theme;"
        "print(json.dumps([derive_theme(h) for h in %r]))"
    ) % (str(src), random_hexes(200))
    out = subprocess.run(
        [sys.executable, "-c", prog], capture_output=True, text=True, check=True
    )
    theirs = json.loads(out.stdout)
    mine = [derive_theme(h) for h in random_hexes(200)]
    assert theirs == mine, "a second interpreter derived different tokens"


def test_it_is_cached_rather_than_recomputed_per_send():
    """
    §04 asks for values cached per affiliate. Cached on the COLOUR, which is the
    same thing and needs no invalidation: the function is pure, so a hit can
    never be stale, and an affiliate who changes colour simply lands on a
    different entry.
    """
    derive_theme.cache_clear()
    first = derive_theme("#0d9488")
    again = derive_theme("#0d9488")
    assert again == first
    info = derive_theme.cache_info()
    assert info.hits == 1 and info.misses == 1, (
        f"second call did not hit the cache: {info}"
    )

    # and the cache must key on the colour, not collapse everything into one
    assert derive_theme("#dc2626") != first
    assert derive_theme.cache_info().misses == 2


def test_a_caller_who_edits_the_result_cannot_poison_another_affiliate():
    """
    The reason the cached value is not handed out directly. One worker process
    renders many accounts; a caller that merged the tokens into a context and
    then adjusted one entry would, with a shared dict, have changed the palette
    for every later report in that process. It would surface as one affiliate's
    colour in another affiliate's PDF, which is the hardest class of bug here to
    trace back to its cause.
    """
    derive_theme.cache_clear()
    mine = derive_theme("#0d9488")
    mine["primary"] = "#ff0000"
    mine["extra"] = "#ff0000"
    theirs = derive_theme("#0d9488")
    assert theirs["primary"] == "#0d9488"
    assert "extra" not in theirs
    assert derive_theme.cache_info().hits == 1, "and it was still a cache hit"


def test_the_cache_is_not_confused_by_spelling():
    derive_theme.cache_clear()
    a = derive_theme("#0D9488")
    b = derive_theme("#0d9488")
    assert a == b
    # Two spellings are two entries — accepted cost of caching on the raw
    # argument. Pinned so the behaviour is known rather than discovered.
    assert derive_theme.cache_info().misses == 2


# ---------------------------------------------------------------------------
# §4.2 — golden-file lock on the six known themes
# ---------------------------------------------------------------------------

def golden():
    return json.loads(GOLDEN.read_text())["themes"]


@pytest.mark.parametrize("name", list(golden()))
def test_golden_file_lock(name):
    """
    What the six live themes render. A diff here is a change to every affiliate
    on that theme; regenerate with scripts/regen_theme_golden.py only when that
    is the intent.
    """
    want = golden()[name]
    got = derive_theme(want["input"])
    for token in TOKENS:
        assert got[token] == want[token], (
            f"{name}.{token}: {got[token]} now, {want[token]} in the golden file"
        )
    assert round(contrast(got["primary"], WHITE), 2) == want["contrast_primary_on_white"]
    assert round(contrast(got["primary_ink"], WHITE), 2) == want["contrast_ink_on_white"]
    assert round(contrast(got["on_primary"], got["primary"]), 2) == want["contrast_on_primary"]


def test_the_golden_file_covers_the_six_themes_the_plan_measured():
    """
    A golden file with one theme in it passes every test above. Pinned so the
    lock cannot shrink unnoticed.
    """
    assert set(golden()) == {
        "demo_title", "luxury_estates", "coastal", "amber", "lime", "violet",
    }


# ---------------------------------------------------------------------------
# The live defect, pinned by name
# ---------------------------------------------------------------------------

def test_luxury_estates_is_fixed_specifically():
    """
    PINNED BY NAME, because a property test over random colours can pass without
    ever generating #0D9488 — and #0D9488 is the one that is wrong in production
    today, on every listing card in every PDF.

    Three assertions, in the order they matter:
      - the input really does fail. If this stops being true the defect is not
        what we think it is.
      - the ink passes.
      - the ink is still the same teal, not a different colour that happens to
        be readable. A fix that changes Luxury Estates' brand is not a fix.
    """
    t = derive_theme("#0D9488")

    assert contrast("#0d9488", WHITE) == pytest.approx(3.74, abs=0.01), (
        "the shipping colour no longer measures 3.74:1 — re-read the defect "
        "before trusting anything else in this test"
    )
    assert contrast(t["primary_ink"], WHITE) >= AA_NORMAL
    assert t["primary_ink"] == "#0b8378"
    assert hue_gap(hue_of(t["primary_ink"]), hue_of("#0d9488")) < 2.0, (
        "the readable value is no longer the affiliate's teal"
    )
    # the fill itself is untouched: `primary` is the colour they chose
    assert t["primary"] == "#0d9488"


def test_the_three_themes_that_already_pass_are_not_touched():
    """
    A ships invisibly. Demo Title, Coastal and Violet clear AA as they are, so
    their ink must be their primary unchanged — nudging a passing colour would
    be a visible change with no defect behind it.
    """
    for hexv in ("#DC2626", "#0E7490", "#7C3AED"):
        t = derive_theme(hexv)
        assert t["primary_ink"] == normalize_hex(hexv), (
            f"{hexv} already passes at {contrast(hexv, WHITE):.2f}:1 and was "
            f"darkened anyway"
        )


# ---------------------------------------------------------------------------
# Input handling — no silent defaults
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("given,want", [
    ("#0D9488", "#0d9488"),
    ("0d9488", "#0d9488"),
    ("  #0D9488  ", "#0d9488"),
    ("#abc", "#aabbcc"),
    ("ABC", "#aabbcc"),
])
def test_normalize_hex_accepts_the_spellings_that_occur(given, want):
    assert normalize_hex(given) == want


@pytest.mark.parametrize("bad", ["", "#12345", "#gggggg", "rebeccapurple",
                                 "rgb(1,2,3)", None, 0x0D9488, "#0d94880"])
def test_an_unparseable_colour_raises_rather_than_defaulting(bad):
    """
    The alternative — falling back to a default teal — is how an affiliate ships
    somebody else's brand with nothing in the log to say so. Same family as
    every other defect on this board that returns a plausible answer.
    """
    with pytest.raises(ValueError):
        derive_theme(bad)


def test_distinct_colours_stay_distinct():
    """
    THE LAST GUARD. Any function that returns one fixed palette satisfies every
    contrast assertion above.
    """
    palettes = {}
    for hexv in random_hexes(1500):
        key = tuple(derive_theme(hexv)[k] for k in TOKENS)
        palettes.setdefault(key, set()).add(normalize_hex(hexv))
    collisions = {k: v for k, v in palettes.items() if len(v) > 1}
    assert not collisions, f"distinct colours produced identical palettes: {list(collisions.items())[:3]}"
