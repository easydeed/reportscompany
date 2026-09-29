"""Apply one regression at a time to themes.py, run the suite, restore."""
import pathlib, subprocess, sys
SRC = pathlib.Path("apps/worker/src/worker/themes.py")
GOLD = pathlib.Path("apps/worker/tests/golden/themes.json")
pristine_src = SRC.read_text()
pristine_gold = GOLD.read_text()

REGRESSIONS = [
    ("R1 ink always black",
     ('    current = normalize_hex(value)\n    for _ in range(_MAX_STEPS):',
      '    current = normalize_hex(value)\n    return "#000000"\n    for _ in range(_MAX_STEPS):')),
    ("R2 one constant palette for everything",
     ('    p = normalize_hex(primary)\n    return (',
      '    p = normalize_hex(primary)\n    p = "#0d9488"\n    return (')),
    ("R3 on_primary always white",
     ('         WHITE if contrast(WHITE, p) >= contrast(NEAR_BLACK, p) else NEAR_BLACK',
      '         WHITE')),
    ("R4 coarser darkening step (0.5 not 0.94)",
     ('_STEP = 0.94', '_STEP = 0.5')),
    ("R5 no early exit: darken even colours that already pass",
     ('    for _ in range(_MAX_STEPS):\n        if contrast(current, WHITE) >= AA_NORMAL:\n            return current\n        stepped',
      '    for _ in range(_MAX_STEPS):\n        if contrast(current, WHITE) >= AA_NORMAL * 1.3:\n            return current\n        stepped')),
    ("R6 luminance without sRGB linearisation",
     ('    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4',
      '    return c')),
    ("R7 unparseable colour falls back to a default",
     ('        raise ValueError(f"not a hex colour: {value!r}")\n    h = m.group(1).lower()',
      '        return "#0d9488"\n    h = m.group(1).lower()')),
    ("R8 no caching",
     ('@lru_cache(maxsize=512)\ndef _derive', 'def _derive')),
    ("R11 hand out the cached dict instead of a copy",
     ('    return dict(_derive(primary))',
      '    return _SHARED.setdefault(primary, dict(_derive(primary)))\n_SHARED = {}')),
    ("R9 tint alpha 0.06 -> 0.5", ('_TINT_ALPHA = 0.06', '_TINT_ALPHA = 0.5')),
    ("R10 primary_dark x0.78 -> x0.90", ('_scale(p, 0.78)', '_scale(p, 0.90)')),
]

for label, (old, new) in REGRESSIONS:
    s = pristine_src
    n = s.count(old)
    if n != 1:
        print(f"!! {label}: anchor matched {n} times — MUTATION DID NOT APPLY")
        continue
    SRC.write_text(s.replace(old, new))
    assert SRC.read_text() != pristine_src, f"{label}: file unchanged on disk"
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_themes.py", "-q",
                            "--no-header", "-p", "no:cacheprovider"],
                           cwd="apps/worker", capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        print(f"{label}\n   TIMED OUT (regression made a test hang, not fail)")
        SRC.write_text(pristine_src)
        continue
    tail = [l for l in r.stdout.strip().split("\n") if "passed" in l or "failed" in l][-1:]
    names = sorted({l.split("::")[1].split(" ")[0]
                    for l in r.stdout.split("\n") if l.startswith("FAILED")})
    print(f"{label}\n   {tail[0] if tail else '??'}")
    for nm in names[:6]:
        print(f"      caught by: {nm}")
    if not names:
        print("      *** NOTHING CAUGHT IT ***")
    SRC.write_text(pristine_src)

SRC.write_text(pristine_src)
GOLD.write_text(pristine_gold)
