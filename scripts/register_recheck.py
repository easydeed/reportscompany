"""Does each email-side item in master plan §05 still reproduce? Rendered, not read."""
import os, re, sys, collections
sys.path.insert(0, "apps/worker/src")
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.email.template import schedule_email_html

REPORT_TYPES = ["market_snapshot","new_listings","inventory","closed","price_bands",
                "open_houses","new_listings_gallery","featured_listings"]
METRICS = {"total_active":42,"total_closed":18,"months_of_inventory":2.3,
           "median_list_price":825000,"median_close_price":812000,"avg_dom":24,
           "new_listings_7d":11,"sale_to_list_ratio":0.982}
BRAND = {"display_name":"Marisol Ridge Realty","rep_name":"Dana Ortiz",
         "rep_title":"Broker Associate","rep_photo_url":"https://assets.example.test/dana.jpg",
         "rep_phone":"(626) 555-0134","rep_email":"dana@example.test",
         "website_url":"https://marisolridge.example.test",
         "primary_color":"#0d9488"}
LISTINGS = [{"address":f"{i} Oak St","city":"La Verne","price":800000+i*1000,
             "beds":3,"baths":2,"sqft":1800,"photo_url":"https://x.test/p.jpg",
             "status":"Active","dom":i} for i in range(1, 9)]

def render(rt):
    return schedule_email_html(
        account_name="Marisol Ridge Realty", report_type=rt, city="La Verne",
        zip_codes=None, lookback_days=30, metrics=METRICS,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a"*64,
        brand=BRAND, listings=LISTINGS, preset_display_name=None,
        filter_description=None, sender_type="REGULAR",
        total_found=50, total_shown=8, total_available=50, showing=8)

out = {rt: render(rt) for rt in REPORT_TYPES}

def report(bid, desc, fn):
    hits = {rt: fn(h) for rt, h in out.items()}
    bad = {rt: v for rt, v in hits.items() if v}
    status = "REPRODUCES" if bad else "not reproduced"
    print(f"\n{bid}  {status}   {desc}")
    for rt, v in list(bad.items())[:8]:
        print(f"     {rt:22s} {v}")

# B19 — placeholder links
PLACEHOLDERS = ["example.com/report.pdf","example.com/unsubscribe",'href="#"',
                "affiliate@trendyreports-demo.com","trendyreports-demo.com"]
report("B19", "every link is a placeholder",
       lambda h: [p for p in PLACEHOLDERS if p in h] or None)

# B20 — no physical postal address slot
report("B20", "no physical postal address in the footer",
       lambda h: None if ("postal" in h.lower() or re.search(r"\b[A-Z]{2}\s+\d{5}\b", h)) else "no address and no slot marker")

# B21 — tel: URI with parens/spaces
report("B21", "tel: URI contains parentheses or spaces",
       lambda h: (re.findall(r'href="tel:[^"]*[()\s][^"]*"', h) or None))

# B22 — Update Preferences -> href="#"
report("B22", '"Update Preferences" is href="#"',
       lambda h: ("Update Preferences" in h and 'href="#"' in h) or None)

# B23 — email renders as the word "Email"; Realtor used generically
def b23(h):
    probs = []
    if re.search(r'>\s*Email\s*<', h): probs.append('link text is the word "Email"')
    if re.search(r'\bRealtor\b(?!®)', h): probs.append("bare 'Realtor'")
    return probs or None
report("B23", 'agent email shown as "Email"; generic "Realtor"', b23)

# B4 — mobile classes defined but attached to zero elements
def b4(h):
    probs = []
    for cls in ("mobile-stack","metric-card","band-row"):
        defined = f".{cls}" in h
        used = re.search(rf'class="[^"]*\b{cls}\b', h) is not None
        if defined and not used:
            probs.append(f"{cls}: defined, 0 elements")
    return probs or None
report("B4", "mobile classes defined and applied to zero elements", b4)

# B11 — color-scheme: light + dark mode opted out
def b11(h):
    probs = []
    if "color-scheme: light" in h or "color-scheme:light" in h:
        probs.append("color-scheme: light")
    if "prefers-color-scheme" not in h:
        probs.append("no prefers-color-scheme block")
    return probs or None
report("B11", "dark mode opted out rather than designed", b11)

# B3 — the open_houses Quick Take panel
def b3(h):
    return (re.findall(r'#1[dD]4[eE][dD]8', h) or None)
report("B3", "Quick Take label #1D4ED8 on a #DC2626 panel", b3)

# B12 — bare hyphen for an empty cell
report("B12", "empty cell renders as a bare hyphen",
       lambda h: (re.findall(r'>\s*-\s*<', h)[:3] or None))

# size budget
print("\n\nSIZE (Gmail clips at 102 KB; §06 budget is 80 KB)")
for rt in REPORT_TYPES:
    kb = len(out[rt].encode()) / 1024
    print(f"     {rt:22s} {kb:7.1f} KB   {'OVER 102' if kb>102 else ('over 80' if kb>80 else 'ok')}")
