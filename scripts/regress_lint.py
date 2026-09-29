import pathlib, subprocess, sys
SRC = pathlib.Path("scripts/lint_template_colors.py"); pristine = SRC.read_text()
R = [
 ("L1 brand-role regex matches nothing",
  ('BRAND_ROLE_PROPERTY = re.compile(\n    r"--(?:"', 'BRAND_ROLE_PROPERTY = re.compile(\n    r"--(?:zzzznope"')),
 ("L2 brand-adjacent hue window 0",   ("HUE_WINDOW = 15.0", "HUE_WINDOW = 0.0")),
 ("L3 chroma floor 0 (flag every off-white)", ("CHROMA_FLOOR = 16", "CHROMA_FLOOR = 0")),
 ("L4 bare suppression silences the line",
  ('        if "lint-allow-hex" in line and not SUPPRESS.search(line):',
   '        if False:')),
 ("L5 suppression ignores the reason",
  ('SUPPRESS = re.compile(r"lint-allow-hex\\s*:\\s*(?P<reason>\\S.*?)\\s*(?:\\*/|-->|#\\}|$)")',
   'SUPPRESS = re.compile(r"(?P<reason>lint-allow-hex)")')),
 ("L6 status colours exempt everywhere, including brand roles",
  ('            if is_role:\n                findings.append(Finding(rel, i + 1, "BRAND-ROLE", h, line))\n                continue',
   '            if is_role and h not in STATUS_HEXES:\n                findings.append(Finding(rel, i + 1, "BRAND-ROLE", h, line))\n                continue\n            if is_role:\n                continue')),
 ("L7 baseline tolerates any count (ratchet off)",
  ("        excess = n - baseline.get(key, 0)", "        excess = 0 if key in baseline else n")),
 ("L8 3-digit hex not recognised",
  ('HEX = re.compile(r"#(?P<v>[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\\b")',
   'HEX = re.compile(r"#(?P<v>[0-9a-fA-F]{6})\\b")')),
]
for label,(old,new) in R:
    n = pristine.count(old)
    if n != 1:
        print(f"!! {label}: anchor matched {n}x — MUTATION DID NOT APPLY"); continue
    SRC.write_text(pristine.replace(old,new))
    assert SRC.read_text() != pristine
    try:
        r = subprocess.run([sys.executable,"-m","pytest","tests/test_template_color_lint.py",
                            "-q","--no-header","-p","no:cacheprovider"],
                           capture_output=True,text=True,timeout=120)
        tail=[l for l in r.stdout.strip().split("\n") if "passed" in l or "failed" in l or "error" in l][-1:]
        names=sorted({l.split("::")[1].split(" ")[0] for l in r.stdout.split("\n") if l.startswith("FAILED")})
        print(f"{label}\n   {tail[0] if tail else '??'}")
        for nm in names[:5]: print(f"      caught by: {nm}")
        if not names: print("      *** NOTHING CAUGHT IT ***")
    except subprocess.TimeoutExpired:
        print(f"{label}\n   TIMED OUT")
    SRC.write_text(pristine)
SRC.write_text(pristine)
