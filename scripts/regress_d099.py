import pathlib, subprocess, sys
SRC = pathlib.Path("apps/worker/src/worker/property_builder.py"); pristine = SRC.read_text()
R = [
 ("P1 target back to 3.0", ("AA_NORMAL = 4.5", "AA_NORMAL = 3.0")),
 ("P2 on_light returns black always",
  ('    current = normalize_hex_color(hex_color)\n    bg = normalize_hex_color(light_bg, "#ffffff")',
   '    return "#000000"\n    current = normalize_hex_color(hex_color)\n    bg = normalize_hex_color(light_bg, "#ffffff")')),
 ("P3 on_dark returns white always",
  ('    current = normalize_hex_color(hex_color)\n    backgrounds = _surfaces(dark_bg)',
   '    return "#ffffff"\n    current = normalize_hex_color(hex_color)\n    backgrounds = _surfaces(dark_bg)')),
 ("P4 unreachable target no longer reported",
  ('    if achieved < AA_NORMAL:\n        _report_unreachable("on_dark", hex_color, "/".join(backgrounds), achieved)',
   '    if False:\n        _report_unreachable("on_dark", hex_color, "/".join(backgrounds), achieved)')),
 ("P5 _brighten desaturates on every step (the old behaviour)",
  ('    if v >= 1.0:\n        s = max(0.0, s - 0.04)\n    else:\n        v = min(1.0, v + 0.04)',
   '    s = max(0.0, s - 0.04)\n    v = min(1.0, v + 0.04)')),
 ("P6 _text_on_accent back to the luminance threshold",
  ('    return _best_of(("#ffffff", "#14151a"), normalize_hex_color(hex_color))',
   '    r, g, b = _hex_to_rgb(hex_color)\n    return "#ffffff" if _relative_luminance(r, g, b) < 0.35 else "#1a1a1a"')),
 ("P7 gradient binds on the first stop only",
  ('    worst = lambda c: min(_contrast(c, b) for b in backgrounds)  # noqa: E731',
   '    worst = lambda c: _contrast(c, backgrounds[0])  # noqa: E731')),
 ("P8 a passing colour is stepped anyway",
  ('    for _ in range(_READABILITY_MAX_STEPS):\n        if worst(current) >= AA_NORMAL:\n            return current',
   '    for _ in range(_READABILITY_MAX_STEPS):\n        if False:\n            return current')),
 ("P9 contrast no longer uses the token layer",
  ('    from .themes import contrast as _themes_contrast\n    return _themes_contrast(a, b)',
   '    ra, ga, ba = _hex_to_rgb(a)\n    rb, gb, bb = _hex_to_rgb(b)\n    la, lb = _relative_luminance(ra,ga,ba), _relative_luminance(rb,gb,bb)\n    return (max(la,lb) + 0.05) / (min(la,lb) + 0.05) * 1.15')),
]
TESTS = ["tests/test_color_roles.py","tests/test_brand_color_validation.py","tests/test_theme_cover_title.py"]
for label,(old,new) in R:
    n = pristine.count(old)
    if n != 1:
        print(f"!! {label}: anchor matched {n} — MUTATION DID NOT APPLY"); continue
    SRC.write_text(pristine.replace(old,new))
    assert SRC.read_text() != pristine
    try:
        r = subprocess.run([sys.executable,"-m","pytest",*TESTS,"-q","--no-header","-p","no:cacheprovider"],
                           cwd="apps/worker", capture_output=True, text=True, timeout=200)
        tail=[l for l in r.stdout.strip().split("\n") if "passed" in l or "failed" in l or "error" in l][-1:]
        names=sorted({l.split("::")[1].split(" ")[0].split("[")[0] for l in r.stdout.split("\n") if l.startswith("FAILED")})
        print(f"{label}\n   {tail[0] if tail else '?? '+r.stdout.strip()[-80:]}")
        for nm in names[:4]: print(f"      caught by: {nm}")
        if not names and not any("error" in (t or "") for t in tail): print("      *** NOTHING CAUGHT IT ***")
    except subprocess.TimeoutExpired:
        print(f"{label}\n   TIMED OUT")
    SRC.write_text(pristine)
SRC.write_text(pristine)
