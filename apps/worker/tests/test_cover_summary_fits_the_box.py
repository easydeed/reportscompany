"""D-349 — the cover's "In short" summary is written to fit the box it goes in.

The prompt asked for the retired overview page's executive summary, "4-5 short
paragraphs, 180-250 words", and nothing trimmed it, so every AI-written cover
showed its introduction and stopped: cut after four lines before Design's T2,
on an ellipsis after five since. The box is not changed (owner, 2026-11-04);
the summary is.

Red on main: the prompt asks for 180-250 words, `max_tokens` is 500, and a
1,500-character reply reaches the cover whole.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))
sys.path.insert(0, str(ROOT / "apps/worker/tests"))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")

from worker import ai_overview  # noqa: E402

SRC = (ROOT / "apps/worker/src/worker/ai_overview.py").read_text(encoding="utf-8")
REQUIRE = os.environ.get("PDF_CONTRAST_REQUIRE_BROWSER") == "1"

#: What the old prompt produced: five paragraphs, ~1,100 characters.
LONG_REPLY = "\n\n".join([
    "This report looks at 1358 5th Street in La Verne and the homes like it that sold nearby.",
    "Your home has two bedrooms and one bathroom across 786 square feet, on a lot larger than most.",
    "Four comparable homes closed recently, between $470,000 and $635,000, most within three weeks.",
    "Inventory in the area is tight, which tends to favour sellers and brings offers in quickly.",
    "Take a look through the full report, and reach out to your agent with any questions you have.",
] * 2)


def test_the_prompt_asks_for_what_fits():
    prompt = ai_overview.SYSTEM_PROMPT
    assert "180-250 words" not in prompt and "4-5" not in prompt
    assert f"at most {ai_overview.SUMMARY_TARGET_CHARS} characters" in prompt
    assert "ONE paragraph" in prompt
    assert ai_overview.SUMMARY_TARGET_CHARS < ai_overview.SUMMARY_MAX_CHARS <= 336
    user = ai_overview._build_prompt({"address": "1358 5th Street"}, {}, {}, [], None)
    assert "180-250 words" not in user and "4-5" not in user
    assert f"at most {ai_overview.SUMMARY_TARGET_CHARS} characters" in user


def test_the_prompt_asks_for_no_value_for_the_home():
    """The estimate lives in the range panel with its method, and nowhere else."""
    assert "Do NOT state a value, price or estimate for the reader's home" in ai_overview.SYSTEM_PROMPT


def test_the_model_is_not_given_room_for_an_essay():
    tokens = int(re.search(r'"max_tokens":\s*(\d+)', SRC).group(1))
    assert tokens <= 150, f"max_tokens {tokens} leaves room for paragraphs the box cannot hold"


def test_a_long_reply_is_cut_at_a_sentence_that_fits():
    text = ai_overview.fit_summary(LONG_REPLY)
    assert len(text) <= ai_overview.SUMMARY_MAX_CHARS
    assert text.endswith(".") and "\n" not in text
    assert text.startswith("This report looks at 1358 5th Street")


def test_a_short_reply_is_left_alone():
    assert ai_overview.fit_summary("  Four homes sold.\n\nMost in three weeks.  ") == \
        "Four homes sold. Most in three weeks."


def test_generation_returns_what_fits(monkeypatch):
    class _Resp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": LONG_REPLY}}]}
    import httpx
    sent = {}
    def _post(url, **kw):
        sent.update(kw["json"])
        return _Resp()
    monkeypatch.setattr(ai_overview, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "post", _post)
    out = ai_overview.generate_overview({"address": "1358 5th Street"}, {}, {}, [], None)
    assert out and len(out) <= ai_overview.SUMMARY_MAX_CHARS
    assert sent["max_tokens"] <= 150


# ── measured: the ceiling fits five lines on every live theme ────────────────
JS = r"""
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [dir, exe, out] = process.argv.slice(2);
  const b = await chromium.launch(exe ? { executablePath: exe } : {}); const p = await b.newPage(); const r = {};
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.html'))) {
    await p.goto('file://' + path.join(dir, f)); await p.evaluate(() => document.fonts.ready);
    r[f] = await p.evaluate(() => { const e = document.querySelector('.inshort-text');
      return Math.round(e.scrollHeight / parseFloat(getComputedStyle(e).lineHeight)); });
  }
  fs.writeFileSync(out, JSON.stringify(r)); await b.close();
})();
"""


def test_the_ceiling_fits_five_lines_on_every_theme():
    if not shutil.which("node"):
        if REQUIRE:
            pytest.fail("node is required for the measurement (PDF_CONTRAST_REQUIRE_BROWSER=1)")
        pytest.skip("node not available")
    from measure_pdf_contrast import find_chromium
    from worker.property_builder import PropertyReportBuilder
    from test_property_production_render import report_data
    PropertyReportBuilder._fetch_market_trends = lambda self: None
    # A worst-case sentence at the ceiling: figures and capitals are the wide glyphs.
    unit = "In La Verne, 4 HOMES like yours SOLD between $470,000 and $635,000, most within 21 days. "
    text = (unit * 6)[:ai_overview.SUMMARY_MAX_CHARS].rsplit(" ", 1)[0]
    work = Path(tempfile.mkdtemp(prefix="inshort-"))
    for theme in ("harbor", "linen", "atlas"):
        d = report_data(theme)
        d["overview_text"] = text
        (work / f"{theme}.html").write_text(PropertyReportBuilder(d).render_html(), encoding="utf-8")
    js, out = ROOT / "_measure_inshort.js", work / "lines.json"
    js.write_text(JS)
    try:
        subprocess.run(["node", str(js), str(work), find_chromium(), str(out)], cwd=str(ROOT), check=True)
    finally:
        js.unlink(missing_ok=True)
    lines = json.loads(out.read_text())
    assert all(n <= 5 for n in lines.values()), (
        f"{len(text)} characters runs past the box's five lines: {lines}")
