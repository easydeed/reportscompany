import re, sys, collections
src = open("docs/DEFECT_LIST.md").read()
entries = re.findall(r"^### (D-\d{3}) — (.*)$", src, re.M)
blocks = re.split(r"^### (?=D-\d{3} —)", src, flags=re.M)
status = {}
sev = {}
for b in blocks[1:]:
    m = re.match(r"(D-\d{3}) —", b)
    if not m: continue
    did = m.group(1)
    s = re.search(r"\*\*Status:\*\*\s*`([a-z-]+)`", b)
    v = re.search(r"\*\*Severity:\*\*\s*([A-Z-]+)", b)
    status[did] = s.group(1) if s else "MISSING"
    sev[did] = v.group(1) if v else "MISSING"
ids = sorted(status)
c = collections.Counter(status.values())
print("total", len(ids), "first", ids[0], "last", ids[-1])
nums = [int(i[2:]) for i in ids]
missing = [n for n in range(nums[0], nums[-1]+1) if n not in nums]
dupes = [i for i,n in collections.Counter(ids).items() if n>1]
print("missing", missing, "dupes", dupes)
for k in ("recorded","open","fixed","closed-not-live","MISSING"):
    print(f"  {k}: {c.get(k,0)}")
opensev = collections.Counter(sev[i] for i in ids if status[i]=="open")
print("open by severity:", dict(opensev), "sum", sum(opensev.values()))
