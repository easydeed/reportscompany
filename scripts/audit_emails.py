import os, sys, collections
sys.path.insert(0, "apps/worker/src"); sys.path.insert(0, "apps/worker/tests")
os.environ.setdefault("AI_INSIGHTS_ENABLED","false"); os.environ.setdefault("DATABASE_URL","postgresql://fake/fake")
os.environ.setdefault("REDIS_URL","redis://localhost:6379/0")
import logging; logging.disable(logging.CRITICAL)
from worker.email.template import schedule_email_html
from _contrast_audit import audit, coverage

RT = ["market_snapshot","new_listings","inventory","closed","price_bands",
      "open_houses","new_listings_gallery","featured_listings"]
THEMES = [("Demo Title","#DC2626"),("Luxury Estates","#0D9488"),("Coastal","#0E7490"),
          ("Amber","#F59E0B"),("Lime","#84CC16"),("Violet","#7C3AED"),("no brand set",None)]
M = {"total_active":42,"total_closed":18,"months_of_inventory":2.3,"median_list_price":825000,
     "median_close_price":812000,"avg_dom":24,"new_listings_7d":11,"sale_to_list_ratio":0.982}
L = [{"street_address":f"{i} Oak St","city":"La Verne","list_price":800000+i*1000,
      "close_price":790000+i*1000,"bedrooms":3,"bathrooms":2,"sqft":1800,
      "photo_url":"https://x.test/p.jpg","status":"Active","days_on_market":i} for i in range(1,9)]

def render(rt, primary):
    b = {"display_name":"Marisol Ridge Realty","rep_name":"Dana Ortiz","rep_title":"Broker Associate",
         "rep_phone":"(626) 555-0134","rep_email":"dana@example.test","website_url":"https://m.example.test"}
    if primary: b["primary_color"] = primary; b["accent_color"] = primary
    return schedule_email_html(account_name="Marisol Ridge Realty", report_type=rt, city="La Verne",
        zip_codes=None, lookback_days=30, metrics=M, pdf_url="https://x.test/a.pdf",
        unsubscribe_url="https://x.test/u?token="+"a"*64, brand=b, listings=L,
        sender_type="REGULAR", total_found=50, total_shown=8)

tot = collections.Counter(); worst = {}; cov = {}
per_pair = collections.Counter()
for name, hx in THEMES:
    n = 0
    for rt in RT:
        html = render(rt, hx)
        meas, decl = coverage(html)
        cov[name] = (cov.get(name,(0,0))[0]+meas, cov.get(name,(0,0))[1]+decl)
        bad = audit(html)
        n += len(bad)
        for f in bad:
            per_pair[(f.fg, f.bg, round(f.ratio,2))] += 1
        if bad and (name not in worst or bad[0].ratio < worst[name].ratio):
            worst[name] = bad[0]
    tot[name] = n
print(f"{'brand':18s} {'failing text runs (8 report types)':36s} worst")
for name, hx in THEMES:
    w = worst.get(name)
    print(f"{name:18s} {tot[name]:>6d}{'':30s} {str(w) if w else '-'}")
print(f"\nTOTAL failing text runs across 7 brands x 8 types: {sum(tot.values())}")
tm = sum(v[0] for v in cov.values()); td = sum(v[1] for v in cov.values())
print(f"COVERAGE: {tm} text/background pairs measured, {td} declined as unresolvable")
print("\nDistinct failing (text, background) pairs, most frequent first:")
for (fg,bg,r), n in per_pair.most_common(18):
    print(f"   {r:5.2f}:1  {fg} on {bg}   x{n}")
