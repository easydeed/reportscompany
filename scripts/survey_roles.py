"""Where does each *-light / *-on-dark token actually get painted?"""
import re, pathlib, collections

VARS = re.compile(r"var\(\s*(--[a-z0-9-]*(?:-light|-on-dark))\s*[,)]", re.I)
# the CSS property the var() sits in: nearest "prop:" to the left on the line
PROP = re.compile(r"([a-z-]+)\s*:\s*[^;{]*$", re.I)

TEXT_PROPS = {"color", "-webkit-text-fill-color", "caret-color"}
DECOR_PROPS = {"background", "background-color", "background-image", "border",
               "border-color", "border-top", "border-bottom", "border-left",
               "border-right", "border-top-color", "border-bottom-color",
               "border-left-color", "border-right-color", "outline", "box-shadow",
               "fill", "stroke", "--x", "text-decoration-color", "column-rule"}

roots = ["apps/worker/src/worker/templates", "apps/web/templates"]
usage = collections.defaultdict(list)
for root in roots:
    for p in sorted(pathlib.Path(root).rglob("*")):
        if not p.is_file():
            continue
        lines = p.read_text().split("\n")
        # track nearest preceding selector line
        sel = ""
        for i, line in enumerate(lines):
            st = line.strip()
            if st.endswith("{") and not st.startswith("@"):
                sel = st[:-1].strip()
            for m in VARS.finditer(line):
                var = m.group(1).lower()
                head = line[:m.start()]
                pm = PROP.search(head)
                prop = pm.group(1).lower() if pm else "?"
                usage[var].append((str(p).split("templates/")[-1], i + 1, prop, sel[:54]))

for var in sorted(usage):
    rows = usage[var]
    props = collections.Counter(r[2] for r in rows)
    text = sum(n for pr, n in props.items() if pr in TEXT_PROPS)
    decor = sum(n for pr, n in props.items() if pr in DECOR_PROPS)
    other = len(rows) - text - decor
    flag = "TEXT" if text else ("decorative" if other == 0 else "mixed/unknown")
    print(f"\n{var}   {len(rows)} uses   text={text} decorative={decor} unclassified={other}   -> {flag}")
    for f, ln, prop, sel in rows:
        mark = "  <-- TEXT" if prop in TEXT_PROPS else ("" if prop in DECOR_PROPS else "  <-- ?")
        print(f"     {f}:{ln:<5} {prop:<22} {sel}{mark}")
