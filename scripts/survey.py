import re, colorsys, collections, pathlib, sys
HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
def norm(h):
    h = h.lower()
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    return "#" + h
def hsl(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i+2],16)/255 for i in (0,2,4))
    hh, l, s = colorsys.rgb_to_hls(r,g,b)
    return hh*360, s, l
roots = ["apps/worker/src/worker/templates", "apps/web/templates"]
per = collections.Counter()
files = collections.defaultdict(collections.Counter)
for root in roots:
    for p in sorted(pathlib.Path(root).rglob("*")):
        if not p.is_file(): continue
        for line in p.read_text().split("\n"):
            for m in HEX.finditer(line):
                c = norm(m.group(1))
                per[c] += 1
                files[str(p)][c] += 1
print("distinct:", len(per), "total:", sum(per.values()))
for c, n in per.most_common():
    hh, s, l = hsl(c)
    tag = "NEUTRAL" if s < 0.15 else ("CHROMATIC")
    print(f"{c}  n={n:3d}  h={hh:6.1f} s={s:.2f} l={l:.2f}  {tag}")
