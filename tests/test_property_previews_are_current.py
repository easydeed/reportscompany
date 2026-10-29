"""The property-report preview images are exactly what the product asks for,
made from a fixed fictional fixture, with no vendor in the loop.

Before 2026-10-29 apps/web/public/previews held five themes x nine pages
screenshotted from HTML that gen_la_verne_all_themes.py built from live
vendor data: two retired themes, four retired pages, and no `notes` page —
the wizard asked for `/previews/pages/{id}/notes.jpg`, got a 404, and its
onError hid the tile. The five pages it did show were the old designs.

`scripts/render_property_previews.py` now renders the live themes' six pages
with the production builder from `scripts/fixtures/property_preview.json`.
This holds the folder, the fixture and the generator to that.
"""
import importlib.util
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps/web/public/previews"
FIXTURE = ROOT / "scripts/fixtures/property_preview.json"
GEN = ROOT / "scripts/render_property_previews.py"
SHOOTER = ROOT / "scripts/render_property_previews.mjs"
WEB = ROOT / "apps/web"


def _gen():
    spec = importlib.util.spec_from_file_location("_render_property_previews", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _jpeg_size(path: Path):
    """(width, height) from the first SOF marker."""
    data = path.read_bytes()
    assert data[:2] == b"\xff\xd8", f"{path.name} is not a JPEG"
    i = 2
    while i < len(data):
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise AssertionError(f"{path.name}: no frame header")


def test_the_folder_is_exactly_the_live_themes_six_pages_and_covers():
    gen = _gen()
    expected = gen.expected_files()
    present = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}
    assert present - expected == set(), f"retired images still shipped: {sorted(present - expected)}"
    assert expected - present == set(), f"images the product asks for and does not have: {sorted(expected - present)}"


def test_the_expected_set_is_the_registry_and_the_builder():
    """POSITIVE CONTROL: the set is computed, not written here."""
    gen = _gen()
    assert [i for i, _ in gen.live_themes()] == [2, 3, 5]
    assert gen.page_order() == ["cover", "property", "comparables", "range", "market_trends", "notes"]
    assert len(gen.expected_files()) == 3 + 3 * 6


def test_every_image_is_a_letter_page_at_510_by_660():
    for p in OUT.rglob("*.jpg"):
        assert _jpeg_size(p) == (510, 660), p.relative_to(OUT)


def test_the_wizard_asks_for_the_pages_that_exist():
    """step-theme.tsx builds `/previews/pages/{theme}/{page.id}.jpg` from
    REPORT_PAGES; every id must have an image for every live theme."""
    types = (WEB / "components/property-wizard/types.ts").read_text(encoding="utf-8")
    block = types[types.index("= [", types.index("export const REPORT_PAGES")):]
    block = block[:block.index("\n]")]
    ids = re.findall(r'id:\s*"(\w+)"', block)
    assert ids, "REPORT_PAGES not parsed"
    for tid, _ in _gen().live_themes():
        for pid in ids:
            assert (OUT / "pages" / str(tid) / f"{pid}.jpg").is_file(), f"/previews/pages/{tid}/{pid}.jpg"
    assert "`/previews/pages/${selectedThemeId}/${page.id}.jpg`" in (
        WEB / "components/property-wizard/step-theme.tsx").read_text(encoding="utf-8")


def test_every_literal_preview_path_in_the_web_app_exists():
    refs = set()
    for f in list(WEB.glob("app/**/*.tsx")) + list(WEB.glob("components/**/*.ts*")) + list(WEB.glob("lib/**/*.ts")):
        refs.update(re.findall(r'"/previews/([\w/]+\.jpg)"', f.read_text(encoding="utf-8")))
    assert refs, "no /previews/ references found"
    assert all((OUT / r).is_file() for r in refs), sorted(r for r in refs if not (OUT / r).is_file())


def test_the_fixture_identifies_no_one():
    """Public images every user sees: no real address, owner, APN or agent."""
    d = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert d["owner_name"] is None and d["apn"] is None and d["legal_description"] is None
    assert not {"secondary_owner", "mailing_address", "owner_name"} & set(d["sitex_data"])
    addresses = [d["property_address"]] + [c["address"] for c in d["comparables"]]
    assert all(re.search(r"\b(Sample|Example|Placeholder)\b", a) for a in addresses), addresses
    assert d["property_city"] == "Anytown" and d["agent"]["email"].endswith("@example.com")


def test_the_generator_calls_no_vendor():
    src = GEN.read_text(encoding="utf-8") + SHOOTER.read_text(encoding="utf-8")
    code = re.sub(r'"""[\s\S]*?"""', "", src)          # the docstring may name what it replaced
    code = re.sub(r"(?m)^\s*(#|//).*$", "", code)
    for vendor in ("simplyrets", "sitex", "fetch_properties", "pdfshift", "_API_KEY", "boto3", "r2"):
        assert vendor not in code.lower(), f"the preview generator reaches {vendor!r}"
    assert "property_preview.json" in src


def test_the_old_live_data_generators_are_gone():
    for name in ("generate_theme_previews.py", "generate_page_preview_jpgs.py", "generate_theme_preview_jpgs.py"):
        assert not (ROOT / "scripts" / name).exists(), name
