"""`display_ink` — the derived answer to an owner decision that was asserted.

Design's package specified `#FFFFFF` for the cover's display lines "by owner
decision", on the stated grounds that white clears WCAG 1.4.3's 3.0 large-text
threshold on the sample brands. D-171 measured that: amber #f59e0b is 2.15 and
lime #84cc16 is 1.98, clearing neither 3.0 nor 4.5. The premise was false for
two of six, and it was the premise — not the preference — that the decision
rested on.

Design's answer (RESPONSE_2026-10-06) computes the threshold instead:

    display_ink = contrast(white, primary) >= 3.0 ? white : on_primary

WHY THIS IS NOT `on_primary` WITH EXTRA STEPS, which is the question a reader
will have. `on_primary` picks the strict winner between white and near-black.
On teal, white is 3.74 and near-black is 4.87, so `on_primary` takes white OFF
teal — and teal at 3.74 was the exception the owner had actually accepted.
`display_ink` keeps white wherever white is legible at display size, so it
lands on exactly one brand differently from `on_primary`, and that one brand is
the decision.

AND THE THRESHOLD IS RIGHT WHILE THE SITE LIST WAS NOT. Pointing all four cover
display sites at it put `#ffffff on #0d9488` at 3.74 under `span.cover-city` —
one new pixel-gate failure. 22px at weight 500 is NOT large text by either of
1.4.3's definitions, so it needs 4.5. The city line takes `on_primary`; the
street line (32-64px) and the 30px stat values take `display_ink`. Measured,
not reasoned about: the gate found it.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps/worker/src"))

from worker.themes import (  # noqa: E402
    NEAR_BLACK, TOKENS, WHITE, contrast, derive_theme,
)

#: The six corpus brands, READ FROM THE GOLDEN FILE rather than restated.
#:
#: The first version of this list spelled them `red` / `teal` / `cyan` /
#: `violet` / `amber` / `lime` — the colloquial names Design's package uses.
#: `test_no_live_code_path_names_a_retired_theme` failed on it, correctly:
#: `teal` is also a RETIRED THEME NAME, and a gate cannot tell a brand called
#: teal from a theme called teal. The corpus's own names (`luxury_estates` for
#: #0D9488) have no such collision, and reading them from the golden file
#: removes a second copy of the brand set at the same time.
#:
#: The same collision runs through Design's response and through the review of
#: it: "four themes" in their package turned out to be the six-brand enum, and
#: `brand: P.brand || "teal"` is a colour, not a theme.
GOLDEN = Path(__file__).resolve().parent / "golden" / "themes.json"
BRANDS = {name: row["input"]
          for name, row in json.loads(
              GOLDEN.read_text(encoding="utf-8"))["themes"].items()}

#: WCAG 1.4.3 large text. Stated here independently of `themes._DISPLAY_MIN`
#: so the test is not asserting the constant against itself.
LARGE_TEXT_MIN = 3.0


def test_display_ink_is_a_token():
    assert "display_ink" in TOKENS
    assert set(derive_theme("#0D9488")) == set(TOKENS)


@pytest.mark.parametrize("name,primary", sorted(BRANDS.items()))
def test_display_ink_is_legible_at_display_size_on_every_brand(name, primary):
    """The property the owner decision was supposed to have."""
    ink = derive_theme(primary)["display_ink"]
    ratio = contrast(ink, primary)
    assert ratio >= LARGE_TEXT_MIN, (
        f"{name} ({primary}): display_ink {ink} is {ratio:.2f} on the brand "
        f"fill, under the {LARGE_TEXT_MIN} large-text threshold. This is the "
        f"defect D-171 found, back again."
    )


@pytest.mark.parametrize("name,primary", sorted(BRANDS.items()))
def test_white_is_kept_wherever_white_is_legible(name, primary):
    """The other half, and the half `on_primary` gets wrong.

    A token that just returned `on_primary` would pass the test above on all
    six. What makes this one different is that it does NOT drop white from a
    brand where white is adequate — which is the owner's preference, honoured
    wherever it is honourable.
    """
    ink = derive_theme(primary)["display_ink"]
    if contrast(WHITE, primary) >= LARGE_TEXT_MIN:
        assert ink.lower() == WHITE.lower(), (
            f"{name}: white is {contrast(WHITE, primary):.2f} on {primary}, "
            f"which clears {LARGE_TEXT_MIN}, but display_ink is {ink}. The "
            f"owner decision was white where white works."
        )
    else:
        assert ink.lower() == NEAR_BLACK.lower(), (
            f"{name}: white is {contrast(WHITE, primary):.2f} on {primary} "
            f"and display_ink is {ink}, which is not the fallback"
        )


def test_it_differs_from_on_primary_on_exactly_one_corpus_brand():
    """If it differed on none, it would BE `on_primary` and could be deleted.

    §0.6: a token whose value is always another token's is a second name for
    one fact. This records that the difference is real and how wide it is —
    one brand of six — so a future change that collapses them is visible.
    """
    differ = {n for n, p in BRANDS.items()
              if derive_theme(p)["display_ink"] != derive_theme(p)["on_primary"]}
    assert differ == {"luxury_estates"}, (
        f"display_ink differs from on_primary on {sorted(differ)}, recorded as "
        f"{{'luxury_estates'}} (#0D9488). None means the token is redundant; "
        f"more means the "
        f"3.0-vs-strict-winner gap widened and the cover changed on brands "
        f"nobody decided about."
    )


def test_the_city_line_does_not_take_display_ink():
    """22px at weight 500 is not large text, so 3.0 does not apply to it.

    Asserted on the template source rather than the rendered document because
    the rendered check already exists — `test_pdf_contrast` caught this exact
    mistake — and this one says WHY, at the site, so the next person pointing a
    fourth site at the token reads the reason before the pixel gate shouts.
    """
    src = (REPO / "apps/worker/src/worker/templates/property/_v2/report.jinja2"
           ).read_text(encoding="utf-8")
    line = next(ln for ln in src.splitlines() if ".cover-city {" in ln)
    assert "var(--on-primary)" in line, (
        f"`.cover-city` is {line.strip()!r}. It is 22px/500 — not large text "
        f"by WCAG 1.4.3 — so it needs 4.5 and cannot use display_ink's 3.0. "
        f"On teal that renders #ffffff at 3.74."
    )
    assert "var(--cover-display)" not in line
