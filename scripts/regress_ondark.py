import pathlib, subprocess, sys
SRC = pathlib.Path("apps/worker/src/worker/themes.py"); pristine = SRC.read_text()
R = [
 ("T1 primary_on_dark returns white always",
  ('    current = normalize_hex(value)\n    for _ in range(_MAX_STEPS):\n        if contrast(current, DARK_SURFACE) >= AA_NORMAL:',
   '    return WHITE\n    current = normalize_hex(value)\n    for _ in range(_MAX_STEPS):\n        if contrast(current, DARK_SURFACE) >= AA_NORMAL:')),
 ("T2 _brighten desaturates on every step",
  ('    if v >= 1.0:\n        s = max(0.0, s - 0.04)\n    else:\n        v = min(1.0, v + 0.04)',
   '    s = max(0.0, s - 0.04)\n    v = min(1.0, v + 0.04)')),
 ("T3 DARK_SURFACE back to the brand navy", ('DARK_SURFACE = "#0f172a"', 'DARK_SURFACE = "#18235c"')),
 ("T4 a passing brand is brightened anyway",
  ('        if contrast(current, DARK_SURFACE) >= AA_NORMAL:\n            return current',
   '        if False:\n            return current')),
 ("T5 the sixth token dropped from TOKENS",
  ('TOKENS = ("primary", "primary_dark", "primary_ink", "on_primary", "tint",\n          "primary_on_dark")',
   'TOKENS = ("primary", "primary_dark", "primary_ink", "on_primary", "tint")')),
]
for label,(old,new) in R:
    n = pristine.count(old)
    if n != 1:
        print(f"!! {label}: anchor matched {n} — DID NOT APPLY"); continue
    SRC.write_text(pristine.replace(old,new))
    try:
        r = subprocess.run([sys.executable,"-m","pytest","tests/test_themes.py","-q","--no-header","-p","no:cacheprovider"],
                           cwd="apps/worker", capture_output=True, text=True, timeout=200)
        tail=[l for l in r.stdout.strip().split("\n") if "passed" in l or "failed" in l or "error" in l][-1:]
        names=sorted({l.split("::")[1].split(" ")[0].split("[")[0] for l in r.stdout.split("\n") if l.startswith("FAILED")})
        print(f"{label}\n   {tail[0] if tail else '?? '+r.stdout.strip()[-70:]}")
        for nm in names[:3]: print(f"      caught by: {nm}")
        if not names and not any("error" in (t or "") for t in tail): print("      *** NOTHING CAUGHT IT ***")
    except subprocess.TimeoutExpired: print(f"{label}\n   TIMED OUT")
    SRC.write_text(pristine)
SRC.write_text(pristine)
print("\nrestored:", SRC.read_text() == pristine)
