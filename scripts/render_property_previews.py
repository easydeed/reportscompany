#!/usr/bin/env python3
"""Render the property-report preview images, from a fixed fixture, locally.

The wizard's page picker shows `/previews/pages/{theme_id}/{page}.jpg` for
every page it offers, and the wizard and the agent Branding page show
`/previews/{theme_id}.jpg` per theme. This writes exactly those, and nothing
else, into apps/web/public/previews/:

  * the LIVE themes only, from the theme registry (worker/themes.json);
  * their six pages, from the builder's own `V2_PAGE_ORDER` — the pages the
    report has today, not the retired nine;
  * rendered by the production builder (`PropertyReportBuilder`) from
    `scripts/fixtures/property_preview.json`, a fixed report with fictional
    addresses, plus the worker's `SAMPLE_MARKET_TRENDS` — no SiteX, no MLS,
    no API key, nothing fetched but the templates' web fonts;
  * screenshotted with a local Chromium (render_property_previews.mjs), one
    image per `<section class="sheet sheet-{page}">`, at 510x660 — the
    816x1056 letter page at 0.625.

Anything else in the folder is a retired image and is deleted, so the folder
is always exactly what the product can ask for
(tests/test_property_previews_are_current.py holds it to that).

Usage:
    python scripts/render_property_previews.py
    CHROMIUM=/path/to/chrome python scripts/render_property_previews.py

It replaced generate_theme_preview_jpgs.py and generate_page_preview_jpgs.py,
which screenshotted HTML made by gen_la_verne_all_themes.py from live vendor
data, for five themes and nine pages, two of each retired.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "property_preview.json"
OUT = ROOT / "apps" / "web" / "public" / "previews"
SHOOTER = ROOT / "scripts" / "render_property_previews.mjs"

sys.path.insert(0, str(ROOT / "apps" / "worker" / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")   # imported, never connected
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def live_themes() -> list[tuple[int, str]]:
    reg = json.loads((ROOT / "apps" / "worker" / "src" / "worker" / "themes.json").read_text())
    return [(t["id"], t["name"]) for t in reg["themes"]]


def page_order() -> list[str]:
    from worker.property_builder import PropertyReportBuilder
    return list(PropertyReportBuilder.V2_PAGE_ORDER)


def expected_files() -> set[str]:
    """Every path, relative to OUT, the product asks for."""
    files = set()
    for tid, _ in live_themes():
        files.add(f"{tid}.jpg")
        files.update(f"pages/{tid}/{p}.jpg" for p in page_order())
    return files


def render_html(theme: str) -> str:
    from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
    from worker.property_builder import PropertyReportBuilder
    data = {k: v for k, v in json.loads(FIXTURE.read_text()).items() if not k.startswith("_")}
    data["theme"] = theme
    data["market_trends_data"] = {**SAMPLE_MARKET_TRENDS, "city": data.pop("market_trends_city")}
    return PropertyReportBuilder(data).render_html()


def main() -> None:
    themes = live_themes()
    pages = page_order()
    with tempfile.TemporaryDirectory() as tmp:
        jobs = []
        for tid, name in themes:
            html = Path(tmp) / f"{tid}.html"
            html.write_text(render_html(name), encoding="utf-8")
            jobs.append({"theme_id": tid, "html": str(html), "pages": pages})
        spec = Path(tmp) / "jobs.json"
        spec.write_text(json.dumps({"out": str(OUT), "jobs": jobs}))
        subprocess.run(["node", str(SHOOTER), str(spec)], check=True, cwd=ROOT / "scripts")

    expected = expected_files()
    written = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}
    missing = expected - written
    if missing:
        sys.exit(f"not written: {sorted(missing)}")
    for rel in sorted(written - expected):
        (OUT / rel).unlink()
        print(f"deleted retired {rel}")
    for d in sorted((p for p in OUT.rglob("*") if p.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    print(f"{len(expected)} images for {len(themes)} live themes x {len(pages)} pages + covers")


if __name__ == "__main__":
    main()
