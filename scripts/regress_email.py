import pathlib, subprocess, sys
SRC = pathlib.Path("apps/worker/src/worker/email/template.py"); pristine = SRC.read_text()
AUD = pathlib.Path("apps/worker/tests/_contrast_audit.py"); paud = AUD.read_text()
R = [
 (SRC, "E1 quick take label back to the accent colour",
  ('color: {on_panel}; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85;">Quick Take</p>',
   'color: {accent_color}; text-transform: uppercase; letter-spacing: 1px;">Quick Take</p>')),
 (SRC, "E2 hardcoded white back on the brand fills",
  ('def _on(fill_hex: str) -> str:', 'def _on(fill_hex: str) -> str:\n    return "#ffffff"')),
 (SRC, "E3 ink targets white instead of the darkest card",
  ('DARKEST_LIGHT_SURFACE = "#f1f5f9"', 'DARKEST_LIGHT_SURFACE = "#ffffff"')),
 (SRC, "E4 ink is the raw brand colour",
  ('    ink = derive_theme(brand_hex)["primary_ink"]', '    ink = brand_hex\n    return ink')),
 (SRC, "E5 default brand back to #6366f1",
  ('normalize_hex_color(brand.get("primary_color"), "#4f46e5")',
   'normalize_hex_color(brand.get("primary_color"), "#6366f1")')),
 (SRC, "E6 footer grey back to #9ca3af",
  ('<a href="{unsubscribe_url}" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a>',
   '<a href="{unsubscribe_url}" style="color: #9ca3af; text-decoration: underline;">Unsubscribe</a>')),
 (SRC, "E7 status badge back to #16a34a",
  ('else "#15803d" if badge_lower == "active"', 'else "#16a34a" if badge_lower == "active"')),
 (SRC, "E8 D-085 precedence restored in _median",
  ('    if kind == SOLD:\n        value = close', '    if kind == SOLD:\n        value = close or lst')),
 (SRC, "E9 email pill back to the word Email",
  ('style="{_pill_style(False)}">{rep_email}</a>', 'style="{_pill_style(False)}">Email</a>')),
 (SRC, "E10 metric-card class detached again",
  ('<td width="25%" class="metric-card" style=', '<td width="25%" style=')),
 (SRC, "E11 masthead band back to hardcoded white",
  ('font-size: 24px; font-weight: bold; color: {_role_on_band};">',
   'font-size: 24px; font-weight: bold; color: #ffffff;">')),
 (AUD, "E12 the walker stops resolving ancestor backgrounds",
  ('        if bgs:\n            self._bg_stack.append((bgs, f"<{tag}>"))\n            pushed_bg = True',
   '        if False:\n            self._bg_stack.append((bgs, f"<{tag}>"))\n            pushed_bg = True')),
]
TESTS = ["tests/test_email_contrast.py","tests/test_insight_price_kind.py",
         "tests/test_email_mobile_and_contact.py"]
for target, label, (old, new) in R:
    base = pristine if target is SRC else paud
    n = base.count(old)
    if n != 1:
        print(f"!! {label}: anchor matched {n} — MUTATION DID NOT APPLY"); continue
    target.write_text(base.replace(old, new))
    try:
        r = subprocess.run([sys.executable,"-m","pytest",*TESTS,"-q","--no-header","-p","no:cacheprovider"],
                           cwd="apps/worker", capture_output=True, text=True, timeout=180)
        tail=[l for l in r.stdout.strip().split("\n") if "passed" in l or "failed" in l or "error" in l][-1:]
        names=sorted({l.split("::")[1].split(" ")[0].split("[")[0] for l in r.stdout.split("\n") if l.startswith("FAILED")})
        print(f"{label}\n   {tail[0] if tail else '?? '+r.stdout.strip()[-90:]}")
        for nm in names[:4]: print(f"      caught by: {nm}")
        if not names and "error" not in (tail[0] if tail else ""): print("      *** NOTHING CAUGHT IT ***")
    except subprocess.TimeoutExpired:
        print(f"{label}\n   TIMED OUT")
    target.write_text(base)
SRC.write_text(pristine); AUD.write_text(paud)
