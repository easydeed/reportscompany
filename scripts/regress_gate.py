import pathlib, subprocess, sys
SRC = pathlib.Path("apps/worker/src/worker/email/template.py"); pristine = SRC.read_text()
R = [
 ("G1 a block dropped from one report type (quick take)",
  ('        body += _build_quick_take(quick_take, accent_color, primary_color)\n    return body',
   '        pass\n    return body')),
 ("G2 a block reordered (stats before the hero)",
  ('    body += _build_hero_stat(hero_value, hero_label, primary_color)\n\n    if trend_stats:',
   '    if trend_stats:')),
 ("G3 a colour role swapped back to the raw brand",
  ('    _primary_on_card = _ink(primary_color, "#f8fafc")',
   '    _primary_on_card = primary_color')),
 ("G4 a link target changed",
  ('<a href="{unsubscribe_url}" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a>',
   '<a href="#" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a>')),
 ("G5 a mobile class lost during the move",
  ('<td width="25%" class="metric-card" style=', '<td width="25%" style=')),
 ("G6 whitespace/indentation only (must NOT fire)",
  ('              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">\n                <tr>\n                  <td style="background-color: {primary_color}; padding: 16px 20px; border-radius: 6px;">',
   '\n\n              <table role="presentation"   cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">\n\n                <tr>\n                      <td style="background-color: {primary_color}; padding: 16px 20px; border-radius: 6px;">')),
]
for label,(old,new) in R:
    n = pristine.count(old)
    if n != 1:
        print(f"!! {label}: anchor matched {n} — DID NOT APPLY"); continue
    SRC.write_text(pristine.replace(old,new))
    try:
        r = subprocess.run([sys.executable,"-m","pytest","tests/test_email_render_diff.py","-q","--no-header","-p","no:cacheprovider"],
                           cwd="apps/worker", capture_output=True, text=True, timeout=200)
        tail=[l for l in r.stdout.strip().split("\n") if "passed" in l or "failed" in l or "error" in l][-1:]
        keys=set()
        for l in r.stdout.split("\n"):
            ls=l.strip()
            for k in ("text:","colours:","links:","images:","classes:","structure:","css_vars:"):
                if ls.startswith(k): keys.add(k.rstrip(":"))
        print(f"{label}\n   {tail[0] if tail else '??'}   facts flagged: {sorted(keys) or 'none'}")
    except subprocess.TimeoutExpired: print(f"{label}\n   TIMED OUT")
    SRC.write_text(pristine)
SRC.write_text(pristine)
print("\nrestored:", SRC.read_text() == pristine)
