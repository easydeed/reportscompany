"""The company Branding page reads what GET /v1/company/branding returns,
writes only what PATCH accepts and the company owns, and says only what the
report does (D-320).

The page it replaces offered a theme picker whose choice was never sent and a
logo Remove the PATCH could not save (it keeps a field sent as null). Design's
copy for the new page said the brand colour "is never changed to fix
contrast"; the market report darkens it under white text (D-112).
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "apps/web/lib/company-brand.ts"
PAGE = ROOT / "apps/web/app/app/company/branding/page.tsx"
COMPANY = ROOT / "apps/api/src/api/routes/company.py"
BUILDER = ROOT / "apps/worker/src/worker/market_builder.py"


def _tree():
    return ast.parse(COMPANY.read_text(encoding="utf-8"))


def _get_branding_keys():
    fn = next(n for n in ast.walk(_tree()) if isinstance(n, ast.FunctionDef) and n.name == "get_branding")
    inner = [d for d in ast.walk(fn) if isinstance(d, ast.Dict)
             and any(isinstance(k, ast.Constant) and k.value == "logo_url" for k in d.keys)]
    assert inner, "get_branding builds no branding dict"
    return {k.value for k in inner[0].keys if isinstance(k, ast.Constant)}


def _patch_fields():
    cls = next(n for n in ast.walk(_tree()) if isinstance(n, ast.ClassDef) and n.name == "UpdateBrandingRequest")
    return {s.target.id for s in cls.body if isinstance(s, ast.AnnAssign)}


def _ts_fields(name):
    src = LIB.read_text(encoding="utf-8")
    m = re.search(rf"export type {name} = \{{\n(.*?)\n\}}", src, re.S)
    assert m, name
    return set(re.findall(r"^\s*([a-z_0-9]+)\??\s*:", m.group(1), re.M))


def _patch_type_fields():
    m = re.search(r"export type BrandPatch = Partial<Pick<CompanyBranding,(.*?)>>", LIB.read_text(encoding="utf-8"), re.S)
    assert m
    return set(re.findall(r'"([a-z_0-9]+)"', m.group(1)))


def _code(path):
    """Source without comments: what the page does, not what it says about itself."""
    src = path.read_text(encoding="utf-8")
    return re.sub(r"^\s*//.*$", "", src, flags=re.M)


def test_the_branding_type_is_what_get_branding_returns():
    missing = _ts_fields("CompanyBranding") - _get_branding_keys()
    assert not missing, f"CompanyBranding reads {sorted(missing)}, which GET /v1/company/branding never returns"


def test_the_page_writes_only_what_patch_accepts():
    extra = _patch_type_fields() - _patch_fields()
    assert not extra, f"BrandPatch sends {sorted(extra)}, which PATCH /v1/company/branding does not accept"


def test_the_page_never_writes_a_reps_fields():
    """A rep's photo and contact lines are theirs (Design §Branding)."""
    sent = _patch_type_fields()
    assert not sent & {"rep_photo_url", "contact_line1", "contact_line2", "website_url"}, sent


def test_the_scan_sees_the_fields_it_should():
    """POSITIVE CONTROL."""
    assert {"logo_url", "primary_color", "rep_photo_url"} <= _get_branding_keys()
    assert {"logo_url", "accent_color", "brand_display_name"} <= _patch_fields()
    assert {"logo_url", "primary_color"} <= _patch_type_fields()


def test_no_control_that_cannot_be_saved():
    """D-320: no Remove (a null is kept by the PATCH's COALESCE), no theme
    picker (the PATCH has no theme), no ImageUpload (it carries a Remove)."""
    code = _code(PAGE)
    assert "ImageUpload" not in code
    assert not re.search(r">\s*Remove\b", code)
    assert "theme" not in code.lower()


def test_only_the_admin_gets_the_controls():
    code = _code(PAGE)
    assert "data?.can_manage === true" in code
    assert code.count("canManage") >= 5, "the controls are not each gated on can_manage"
    assert re.search(r"canManage \? \(\s*<div[^>]*>\s*<button type=\"button\" onClick=\{save\}", code), "Save is not gated"


def test_the_contrast_sentence_is_what_the_report_does():
    """The page says the report darkens a colour under white text. That is
    true while the masthead band is built by darken_until_readable; if the
    builder stops, the sentence must change with it."""
    assert "darkens it just enough to read" in _code(PAGE)
    assert "never changed" not in _code(PAGE), "the page repeats Design's untrue sentence"
    fn = next(n for n in ast.walk(ast.parse(BUILDER.read_text(encoding="utf-8")))
              if isinstance(n, ast.FunctionDef) and n.name == "_masthead_band")
    assert "darken_until_readable" in ast.unparse(fn)
