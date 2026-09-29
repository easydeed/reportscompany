import os, re, sys
sys.path.insert(0, "apps/worker/src")
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
import logging; logging.disable(logging.CRITICAL)
from worker.email.template import schedule_email_html
sys.path.insert(0, "apps/worker/src")
from worker.themes import contrast

METRICS = {"total_active":42,"total_closed":18,"months_of_inventory":2.3,
           "median_list_price":825000,"median_close_price":812000,"avg_dom":24}
def render(rt, brand, listings=None):
    return schedule_email_html(account_name="Marisol Ridge Realty", report_type=rt,
        city="La Verne", zip_codes=None, lookback_days=30, metrics=METRICS,
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token="+"a"*64,
        brand=brand, listings=listings, sender_type="REGULAR",
        total_found=50, total_shown=8)

B = {"display_name":"Marisol Ridge Realty","rep_name":"Dana Ortiz","rep_title":"Broker Associate",
     "rep_photo_url":"https://x.test/d.jpg","rep_phone":"(626) 555-0134",
     "rep_email":"dana@example.test","website_url":"https://m.example.test","primary_color":"#0d9488"}

print("="*72)
print("B20 — the postal-address SLOT. Positive control: set a value and see it render.")
print("="*72)
no_addr = render("market_snapshot", B)
with_addr = render("market_snapshot", dict(B, postal_address="742 Evergreen Terrace, Springfield, IL 62704"))
print("  unset  : address string present?", "742 Evergreen" in no_addr)
print("  set    : address string present?", "742 Evergreen" in with_addr)
print("  -> the slot", "EXISTS and is honoured" if "742 Evergreen" in with_addr else "DOES NOT EXIST (key ignored)")
# what did my earlier check match on?
m = re.findall(r"\b[A-Z]{2}\s+\d{5}\b", no_addr)
print("  my earlier ZIP-pattern check matched:", m[:3], "<- why it said 'not reproduced'")

print()
print("="*72)
print("B11 — dark mode. Positive control: show the block that exists.")
print("="*72)
blocks = re.findall(r"@media\s*\(prefers-color-scheme:\s*dark\s*\)", no_addr)
print("  prefers-color-scheme: dark blocks:", len(blocks))
print("  'color-scheme' meta/property occurrences:", re.findall(r"color-scheme[^;\"<]{0,40}", no_addr)[:4])
i = no_addr.find("prefers-color-scheme")
print("  first block, 420 chars:")
print("   ", no_addr[i-60:i+420].replace("\n", "\n    ")[:520])

print()
print("="*72)
print("B3 — open_houses Quick Take. Positive control: does the panel render at all?")
print("="*72)
oh = render("open_houses", B)
print("  'Quick Take' present:", "Quick Take" in oh)
if "Quick Take" in oh:
    j = oh.find("Quick Take")
    seg = oh[max(0,j-700):j+300]
    print("  hexes near it:", sorted(set(re.findall(r"#[0-9a-fA-F]{6}", seg))))
    print("  ...", seg[-320:].replace("\n"," ")[:320])

print()
print("="*72)
print("B12 — empty cells. Positive control: feed a listing with missing fields.")
print("="*72)
holey = [{"address":"1 Oak St","city":"La Verne","price":None,"beds":None,"baths":None,
          "sqft":None,"photo_url":None,"status":None,"dom":None}]
for rt in ("closed","inventory","new_listings"):
    h = render(rt, B, holey)
    bare = re.findall(r">\s*[-–—]\s*<", h)
    nones = re.findall(r">\s*None\s*<", h)
    nodata = re.findall(r">\s*(?:no data|No data|N/A|—)\s*<", h)
    print(f"  {rt:14s} bare-hyphen cells={len(bare)}  'None' cells={len(nones)}  'no data'={len(nodata)}")
