"""The market email's contrast gate, in light AND dark mode, read off the pixel.

WHY THIS FILE EXISTS
--------------------
`test_email_contrast.py` walks inline styles. That is the right tool for the
light document and blind to dark mode by construction: dark mode is a
`@media (prefers-color-scheme: dark)` block of `!important` rules, which no
inline-style walker evaluates. The review of Design's 5th package measured what
it hides — on a navy brand, prices and the hero number at 1.00–1.13:1 on the
dark card, the unsubscribe link at 3.08:1 — in markup that every inline check
passes.

So this renders every report type, for every brand in the audit set plus two
dark ones (dark brands are where dark mode fails), under BOTH colour schemes in
Chromium, and reads the rendered pixel behind every text run
(`scripts/measure_contrast_by_pixel.py`, the method the PDF gate settled on in
D-130 after four wrong readings from DOM-based resolution).

NOT A RATCHET. The PDF gate tolerates a baseline because it started with
1,387 failures. This email starts at zero, so the rule is zero.

WHAT IT DOES NOT SEE
--------------------
Clients differ. Apple Mail and iOS honour the media query; Gmail's apps ignore
it and apply their own inversion, which no headless browser reproduces. This
gate proves the dark palette WE ship is readable, which is the part we control.

A missing browser fails under `PDF_CONTRAST_REQUIRE_BROWSER=1` (set in CI) and
skips locally, the same rule as `test_pdf_contrast.py`, for the same reason: a
gate that goes quiet when its tooling is absent goes quiet exactly when nobody
is watching.
"""
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "apps/worker/src"))

from email_fixtures import REPORT_TYPES, render  # noqa: E402
from test_email_contrast import BRANDS  # noqa: E402

REQUIRE = os.environ.get("PDF_CONTRAST_REQUIRE_BROWSER") == "1"

#: The audit set plus two DARK brands, because dark mode fails on dark brands:
#: a navy ink is fine on white and invisible on the dark card.
DARK_MODE_BRANDS = BRANDS + [("navy", "#1B365D"), ("wine", "#7F1D1D")]

#: The width the email is read at: the 600px card plus the page gutter.
EMAIL_WIDTH = 680

#: Text runs a working measurement finds in ONE email, floored. The smallest
#: (a gallery kind) has ~40; a measurement that finds fewer is broken, not clean.
MIN_RUNS_PER_DOCUMENT = 25


def _pixel():
    spec = importlib.util.spec_from_file_location(
        "_measure_contrast_by_pixel", ROOT / "scripts/measure_contrast_by_pixel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _browser_or_skip(pixel):
    if shutil.which("node") is None:
        reason = "node is not installed"
    else:
        try:
            import subprocess
            subprocess.run(
                ["node", "-e", "require('playwright'); require('pngjs')"],
                cwd=str(ROOT), check=True, capture_output=True)
            return
        except Exception as e:  # noqa: BLE001
            reason = f"playwright/pngjs not loadable: {e}"
    if REQUIRE:
        pytest.fail(f"the email contrast gate cannot run: {reason}")
    pytest.skip(reason)


#: Light mode is also walked, inline, on all eight kinds by
#: `test_email_contrast.py`; here it is measured on one kind per block family
#: (rows, table, bands, cards), which keeps the gate near a minute. Dark mode has
#: no other check, so it gets every kind.
LIGHT_KINDS = ("market_snapshot", "closed", "price_bands", "featured_listings")


def _corpus(kinds=REPORT_TYPES):
    return {f"{brand}__{kind}": render(kind, primary)
            for brand, primary in DARK_MODE_BRANDS for kind in kinds}


def _measure(docs, scheme):
    pixel = _pixel()
    _browser_or_skip(pixel)
    return pixel.score(pixel.measure_docs(docs, scheme=scheme, width=EMAIL_WIDTH))


def _failures(rows):
    return sorted(
        (r for r in rows if r["ratio"] < r["needs"] and not r["unmeasurable"]),
        key=lambda r: r["ratio"])


def _report(fails):
    seen, lines = set(), []
    for r in fails:
        key = (r["doc"].split("__")[0], r["selector"], r["fg_hex"], r["bg_hex"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"  {r['ratio']:.2f}:1 (needs {r['needs']})  {r['doc']:34s} "
                     f"{r['selector'][:28]:28s} {r['fg_hex']} on {r['bg_hex']}  {r['text'][:30]!r}")
    return "\n".join(lines[:40])


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_every_text_run_is_readable(scheme):
    corpus = _corpus(LIGHT_KINDS if scheme == "light" else REPORT_TYPES)
    rows = _measure(corpus, scheme)
    per_doc = {}
    for r in rows:
        per_doc[r["doc"]] = per_doc.get(r["doc"], 0) + 1
    thin = sorted(d for d in corpus if per_doc.get(d, 0) < MIN_RUNS_PER_DOCUMENT)
    assert not thin, (
        f"{scheme}: the measurement found fewer than {MIN_RUNS_PER_DOCUMENT} text "
        f"runs in {thin[:5]} — it is broken, not clean")
    fails = _failures(rows)
    assert not fails, (
        f"{scheme} mode: {len(fails)} text run(s) below their WCAG threshold, "
        f"in {len({r['doc'] for r in fails})} of {len(corpus)} emails:\n" + _report(fails))


def test_the_dark_gate_sees_the_failure_it_exists_for(monkeypatch):
    """
    POSITIVE CONTROL. Put the review's failure back — brand text keeping its
    light-mode ink in dark mode, which is what the email shipped before
    `.tr-brand` — and the gate must report it on the navy brand.
    """
    from worker.email import template as tmpl
    monkeypatch.setattr(tmpl, "_dark_ink", lambda brand_hex: tmpl.derive_theme(brand_hex)["primary_ink"])
    rows = _measure({"navy__market_snapshot": render("market_snapshot", "#1B365D")}, "dark")
    fails = _failures(rows)
    assert any("tr-brand" in r["selector"] for r in fails), (
        "brand text at its light-mode ink on the dark card was not reported — "
        "the dark gate cannot see the failure it was written for")


def test_the_dark_palette_is_actually_applied():
    """
    NEGATIVE CONTROL for the media query itself. If the shell lost
    `prefers-color-scheme`, the dark render would be the light one and the
    gate above would pass by measuring the wrong document.
    """
    rows = _measure({"x": render("market_snapshot", "#0D9488")}, "dark")
    backdrops = {r["bg_hex"].lower() for r in rows}
    assert "#1f2937" in backdrops, (
        f"no text sits on the dark card (#1F2937) under a dark colour scheme — "
        f"the dark-mode rules are not applying. Backdrops seen: {sorted(backdrops)[:8]}")


# ── the home-value email ───────────────────────────────────────────────────

def _home_value_corpus():
    from worker.email.home_value import home_value_email_html
    docs = {}
    for brand, primary in DARK_MODE_BRANDS:
        docs[f"{brand}__home_value"] = home_value_email_html(
            report_url="https://www.trendyreports.io/r/abc", address="14 Sandpiper Ln",
            city="Irvine", requester_first_name="Tom", agent_name="Dana Ortiz",
            agent_title="Broker Associate", company_name="Marisol Ridge Realty",
            agent_phone="(626) 555-0134", agent_email="dana@example.test",
            primary_color=primary)
    return docs


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_the_home_value_email_is_readable(scheme):
    """
    Design's Call / Text buttons had no dark-mode class and measured 1.22:1 on
    the dark card in the review. Every run, both schemes, every brand.
    """
    corpus = _home_value_corpus()
    rows = _measure(corpus, scheme)
    assert len(rows) >= len(corpus) * 15, "the measurement found almost no text"
    fails = _failures(rows)
    assert not fails, f"home-value, {scheme}: {len(fails)} run(s) below AA:\n" + _report(fails)
