import re, collections, pathlib
HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
def norm(h):
    h = h.lower()
    if len(h) == 3: h = "".join(c*2 for c in h)
    return h
def chroma(h):
    h = norm(h.lstrip("#"))
    r,g,b = (int(h[i:i+2],16) for i in (0,2,4))
    return max(r,g,b)-min(r,g,b)
per = collections.Counter()
for root in ("apps/worker/src/worker/templates","apps/web/templates"):
    for p in sorted(pathlib.Path(root).rglob("*")):
        if p.is_file():
            for m in HEX.finditer(p.read_text()):
                per["#"+norm(m.group(1))] += 1
rows = sorted(per.items(), key=lambda kv: chroma(kv[0]))
for c,n in rows:
    print(f"{chroma(c):4d}  {c}  n={n}")
print("---- histogram of chroma ----")
h = collections.Counter(chroma(c)//8*8 for c in per)
for b in sorted(h): print(f"{b:3d}-{b+7:3d}: {'#'*h[b]} ({h[b]})")
