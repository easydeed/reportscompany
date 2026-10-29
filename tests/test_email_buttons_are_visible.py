"""Every email's buttons are visible against the card, in light AND dark (D-313).

The text gates (`test_email_dark_mode.py`, `test_transactional_shell.py`) read
the label against the button and pass: white on navy is 17:1. What they cannot
see is the button against the CARD. In dark mode an ink button (#0F172A) on the
dark card (#1F2937) measured 1.3:1 — the label floats with no button around it
— and a navy brand's "Open the full report" did the same. The button is the one
thing each email asks the reader to press.

THE RULE: WCAG 1.4.11 (non-text contrast), 3:1 for the visual boundary of a
control. A button passes when its fill OR its border clears 3:1 against the
card behind it. Measured in Chromium off computed styles, under both schemes,
for:

  * every account email (the API's senders and the worker's failure notice),
  * the market email, on every audit brand plus the dark ones,
  * the home-value email, on the same brands.

A "button" is any table cell holding a `display:block` link that paints a fill:
found by shape, not by class, so a new button cannot skip the gate by not
carrying the dark-mode class. Outline buttons (home-value Call / Text) are
hairlines by Design's choice and named by their label; they are not held to
3:1, and their dark-mode border is lightened all the same.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/worker/src"))
sys.path.insert(0, str(ROOT / "apps/worker/tests"))
sys.path.insert(0, str(ROOT / "apps/api/src"))
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

NON_TEXT = 3.0

JS = r"""
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [dir, scheme] = process.argv.slice(2);
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 680, height: 900 }, colorScheme: scheme });
  const out = {};
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort()) {
    await page.setContent(fs.readFileSync(path.join(dir, f), 'utf8'), { waitUntil: 'load' });
    out[f.replace(/\.html$/, '')] = await page.evaluate(() => {
      const bgOf = (el) => {
        for (let n = el; n; n = n.parentElement) {
          const c = getComputedStyle(n).backgroundColor;
          if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') return c;
        }
        return 'rgb(255, 255, 255)';
      };
      const rows = [];
      for (const a of document.querySelectorAll('a')) {
        if (getComputedStyle(a).display !== 'block') continue;
        const td = a.closest('td'); if (!td) continue;
        const s = getComputedStyle(td);
        const fill = s.backgroundColor;
        const hasFill = fill && fill !== 'rgba(0, 0, 0, 0)' && fill !== 'transparent';
        const bw = parseFloat(s.borderTopWidth) || 0;
        // Filled buttons only. Outline buttons (home-value Call / Text) are
        // drawn as hairlines by design and identified by their label; their
        // dark border is lightened, but they are not held to 3:1 here.
        if (!hasFill) continue;
        rows.push({ label: a.textContent.trim().slice(0, 40), fill: hasFill ? fill : null,
                    border: bw ? s.borderTopColor : null, borderWidth: bw,
                    card: bgOf(td.parentElement.closest('td, table, body')) });
      }
      // Step discs: a filled cell holding only a number (the onboarding steps).
      for (const td of document.querySelectorAll('td')) {
        if (!/^\d+$/.test(td.textContent.trim()) || td.querySelector('td')) continue;
        const fill = getComputedStyle(td).backgroundColor;
        if (!fill || fill === 'rgba(0, 0, 0, 0)' || fill === 'transparent') continue;
        rows.push({ label: 'step ' + td.textContent.trim(), fill, border: null, borderWidth: 0,
                    card: bgOf(td.parentElement.closest('table').parentElement) });
      }
      return rows;
    });
  }
  console.log(JSON.stringify(out));
  await b.close();
})();
"""


def _lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _rgb(css):
    return tuple(int(float(x)) for x in css[css.index("(") + 1:css.index(")")].split(",")[:3])


def _ratio(a, b):
    la, lb = sorted((_lum(_rgb(a)), _lum(_rgb(b))), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _measure(docs, scheme):
    if shutil.which("node") is None or subprocess.run(
            ["node", "-e", "require('playwright')"], cwd=str(ROOT), capture_output=True).returncode:
        if os.environ.get("PDF_CONTRAST_REQUIRE_BROWSER") == "1":
            pytest.fail("the button visibility gate cannot run: no browser")
        pytest.skip("no browser")
    with tempfile.TemporaryDirectory() as d:
        for name, html in docs.items():
            Path(d, f"{name}.html").write_text(html, encoding="utf-8")
        js = Path(d, "measure.cjs")
        js.write_text(JS)
        res = subprocess.run(["node", str(js), d, scheme], cwd=str(ROOT),
                             capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, res.stderr[-2000:]
    return json.loads(res.stdout.strip().splitlines()[-1])


def _boundary(row):
    """The best of fill-against-card and border-against-card."""
    best = 0.0
    if row["fill"]:
        best = max(best, _ratio(row["fill"], row["card"]))
    if row["border"] and row["borderWidth"] >= 1:
        best = max(best, _ratio(row["border"], row["card"]))
    return best


# ── the corpus ───────────────────────────────────────────────────────────────

def _account_emails():
    from api.services import email as em
    calls = [
        ("send_verification_email", ("a@x.test", "Dana", "t"), {}),
        ("send_password_reset_email", ("a@x.test", "Dana", "t"), {}),
        ("send_role_invite_email", ("a@x.test", "Ben", "Pacific Title", "t"), {"role": "sponsored_agent"}),
        ("send_limit_reached_email", ("a@x.test", "Dana", 25), {"count": 25}),
        ("send_regular_agent_welcome_email", ("a@x.test", "Dana"), {}),
        ("send_rep_welcome_email", ("a@x.test", "Ben", "Pacific Title"), {}),
    ]
    docs = {}
    for fn, a, k in calls:
        sent = {}
        with patch.object(em.email_service, "send_email_sync", lambda **p: sent.update(p) or {"ok": True}), \
             patch.object(em, "_plan_limits", lambda slug: {"market_reports": 3, "schedules": 1}):
            getattr(em, fn)(*a, **k)
        docs[f"account__{fn}"] = sent["html"]
    from worker import tasks
    from worker.email.transactional import _email_base
    _, content, pre = tasks._failure_notice(
        schedule_name="Monthly Irvine Snapshot", area="Irvine", brief_error="x",
        active=True, consecutive_failures=1, schedule_url="https://x.test/app/schedules")
    docs["account__schedule_failed"] = _email_base(content, preheader=pre)
    return docs


def _brand_emails():
    from email_fixtures import render
    from test_email_dark_mode import DARK_MODE_BRANDS
    from worker.email.home_value import home_value_email_html
    docs = {}
    for brand, primary in DARK_MODE_BRANDS:
        docs[f"market__{brand}"] = render("market_snapshot", primary)
        docs[f"home_value__{brand}"] = home_value_email_html(
            report_url="https://www.trendyreports.io/r/abc", address="14 Sandpiper Ln",
            city="Irvine", requester_first_name="Tom", agent_name="Dana Ortiz",
            agent_title="Broker", company_name="Ridge Realty", agent_phone="(626) 555-0134",
            agent_email="dana@example.test", primary_color=primary)
    return docs


@pytest.fixture(scope="module")
def corpus():
    return {**_account_emails(), **_brand_emails()}


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_every_button_is_visible_against_the_card(corpus, scheme):
    found = _measure(corpus, scheme)
    none = sorted(d for d in corpus if not found.get(d))
    assert not none, f"no button found in {none[:6]}: the measurement is not looking"
    fails = [(d, r["label"], round(_boundary(r), 2), r["fill"], r["border"], r["card"])
             for d, rows in found.items() for r in rows if _boundary(r) < NON_TEXT]
    assert not fails, (
        f"{scheme}: {len(fails)} button(s) below {NON_TEXT}:1 against the card:\n  "
        + "\n  ".join(map(str, fails[:20])))


def test_the_gate_sees_the_failure_it_was_written_for(corpus):
    """POSITIVE CONTROL: strip the dark-mode classes, which is the email as it
    shipped before D-313, and the dark measurement must fail on the ink button
    and on a navy brand's button; and the light measurement on a pale brand."""
    stripped = {k: v.replace(' class="tr-fill"', "").replace(' class="tr-fill tr-fill-ink"', "")
                        .replace(' class="tr-edge"', "")
                for k, v in corpus.items()
                if k in ("account__send_verification_email", "market__navy", "home_value__navy")}
    found = _measure(stripped, "dark")
    below = {d for d, rows in found.items() for r in rows if _boundary(r) < NON_TEXT}
    assert {"account__send_verification_email", "market__navy", "home_value__navy"} <= below, below
    discs = {"w": corpus["account__send_regular_agent_welcome_email"].replace(' class="tr-fill tr-fill-ink"', "")}
    found = _measure(discs, "dark")
    assert any(r["label"].startswith("step") and _boundary(r) < NON_TEXT for r in found["w"]), \
        "the step discs are not being measured"
    pale = {k: v.replace("border:2px solid", "border:0px solid") for k, v in corpus.items()
            if k in ("market__amber", "home_value__lime")}
    found = _measure(pale, "light")
    assert {d for d, rows in found.items() for r in rows if _boundary(r) < NON_TEXT} == set(pale)
