Totally — let’s “decode” that Irvine Market Snapshot and turn it into a clear spec you can hand straight to Cursor.

I’ll walk section‑by‑section and tell you:

What data to pull (which query)

How to calculate each metric

Exactly which SimplyRETS fields to use

I’ll assume Last 30 days as your period, but everything works for any lookback.

1. Data pulls you should have in hand

Instead of one giant fuzzy query, think of the snapshot as being built from three core datasets plus a helper for price tiers:

1.1 Closed sales (last 30 days)

Used for:

Median Sale Price (top bar)

Closed Sales (top bar)

Avg Days on Market (top bar)

Sale‑to‑List Ratio (core indicator)

BY PROPERTY TYPE table (all columns)

BY PRICE TIER: Median and Closed

Query (from your guide – Closed Listings Report):

# /properties
{
    'q': city_name,          # e.g. "Irvine"
    'status': 'Closed',
    'mindate': start_date,   # YYYY-MM-DD (closeDate >= mindate)
    'maxdate': end_date,     # YYYY-MM-DD (closeDate <= maxdate)
    'limit': 1000,
    'offset': 0,
    'sort': '-closeDate'
}


Use fields:
sales.closePrice, sales.closeDate, daysOnMarket (or mls.daysOnMarket), listPrice, property.type, property.subType, address.city.

1.2 Active inventory (current snapshot)

Used for:

Months of Inventory (top bar)

BY PRICE TIER: MOI

(Optionally) Active count totals

Query (Inventory Report):

# /properties
{
    'q': city_name,
    'status': 'Active',
    'limit': 1000,
    'offset': 0,
    'sort': 'daysOnMarket'
}


Use fields: listPrice, daysOnMarket, property.type, address.city.

1.3 New listings (last 30 days)

Used for:

CORE INDICATOR: “New Listings”

Query (New Listings Report):

# /properties
{
    'q': city_name,
    'status': 'Active',
    'mindate': start_date,   # filter on listDate
    'maxdate': end_date,
    'limit': 500,
    'offset': 0,
    'sort': '-listDate'
}


Use fields: listDate, listPrice, address.city.

1.4 Pending sales (last 30 days)

Used for:

CORE INDICATOR: “Pending Sales”

Recommended query:

# /properties
{
    'q': city_name,
    'status': 'Pending',
    'mindate': start_date,   # For Pending, SimplyRETS uses list/modified date filters
    'maxdate': end_date,
    'limit': 1000,
    'offset': 0,
    'sort': '-listDate'
}


If you want “went pending in last 30 days” more precisely, also check sales.contractDate in code and filter there when available.

1.5 Optional: Price-band helper (for tiers)

You can reuse your Price Bands Report logic to get price‑segmented active inventory (we’ll just collapse those bands into Entry / Move‑Up / Luxury).

But you don’t strictly need a separate API call; you can also compute tiers directly from the Active + Closed lists you already fetched.

2. Top bar metrics (the four big numbers)

Labels at bottom of your PDF:
Median Sale Price • Closed Sales • Avg. Days on Market • Months of Inventory

Assume:

closings = closed_listings_last_30_days  # from 1.1
active   = active_listings_now           # from 1.2
period_days = (end_date - start_date).days  # usually 30

2.1 Median Sale Price

Filter: use closings

Field: sales.closePrice; if closePrice is missing, fallback to listPrice.

Calc: sort prices and take middle value.

prices = [p.get('sales', {}).get('closePrice') or p['listPrice']
          for p in closings if (p.get('sales', {}) or {}).get('closePrice') or p.get('listPrice')]
prices.sort()
median_sale_price = prices[len(prices)//2] if prices else 0

2.2 Closed Sales

Value: simple count of closings.

closed_sales = len(closings)

2.3 Avg. Days on Market

Use daysOnMarket as documented.

dom_values = [p.get('daysOnMarket') or p.get('mls', {}).get('daysOnMarket', 0)
              for p in closings]
avg_dom = (sum(dom_values) / len(dom_values)) if dom_values else 0

2.4 Months of Inventory (MOI)

Standard real‑estate formula:

MOI = Current Active Listings ÷ (Closed Sales per Month)

For a 30‑day period:

active_count = len(active)
closed_count = len(closings)

if closed_count > 0:
    months_of_inventory = active_count / (closed_count * (30 / period_days))
else:
    months_of_inventory = None  # or show '—' / very high


So with a pure 30‑day lookback, this simplifies to:

months_of_inventory = active_count / closed_count  # if closed_count > 0

3. CORE INDICATORS block

In the PDF: New Listings • Pending Sales • Sale-to-List Ratio (plus % change vs prior period).

Assume:

new_listings = new_listings_last_30_days  # from 1.3
pendings     = pending_listings_30_days   # from 1.4

3.1 New Listings

Count of properties that hit the market in the period.

Use new_listings query (status=Active, mindate/maxdate on listDate).

Value:

new_listings_count = len(new_listings)

3.2 Pending Sales

Two flavors; pick one and be consistent:

Option A (simpler – recommended to start):

Number of listings that are currently Pending and whose list/modified date is within the period.

pending_sales_count = len(pendings)


Option B (more exact “went pending in last 30 days”):

Use same pendings query but then filter by sales.contractDate within start_date..end_date when present.

from datetime import datetime

def in_period(dt_str, start, end):
    if not dt_str:
        return False
    dt = datetime.fromisoformat(dt_str.replace('Z', ''))
    return start <= dt <= end

pending_sales_count = len([
    p for p in pendings
    if in_period(p.get('sales', {}).get('contractDate'), start_date_dt, end_date_dt)
])

3.3 Sale-to-List Ratio

You already have this in the Closed Listings Report logic: avg close‑to‑list ratio.

Sale-to-List Ratio (%) = average of (closePrice ÷ listPrice × 100) for all closings in the period

ratios = []
for p in closings:
    close_price = p.get('sales', {}).get('closePrice')
    list_price  = p.get('listPrice')
    if close_price and list_price:
        ratios.append((close_price / list_price) * 100)

sale_to_list_ratio = (sum(ratios) / len(ratios)) if ratios else 0

3.4 “0%” change values

The right‑hand “0%” in your sample PDF is clearly intended as change vs prior period (e.g., previous 30 days).

Pattern for any metric:

Compute value for current window (start_date..end_date).

Compute same metric for previous window (start_date - period_days .. start_date - 1).

Change %:

def pct_change(current, previous):
    if not previous or previous == 0:
        return 0   # or None / '—' if you prefer
    return round(((current - previous) / previous) * 100, 1)


Use this for:

New Listings

Pending Sales

Sale‑to‑List Ratio

(Optionally) Median Price, Closed Sales, Avg DOM, MOI.

4. BY PROPERTY TYPE table

Columns: Type • Median Price • Closed • DOM

We’ll base this purely on closed sales in the period, grouped by type.

4.1 Map SimplyRETS types → SFR / Condo / Townhome

SimplyRETS uses property.type codes (RES, CND, etc.) plus a human subType like “Single Family Residence”.

Suggested classifier:

def classify_type(p):
    sub = (p.get('property', {}).get('subType') or '').lower()
    type_code = (p.get('property', {}).get('type') or '').upper()

    if 'townhouse' in sub or 'townhome' in sub:
        return 'Townhome'
    if type_code == 'CND' or 'condo' in sub or 'condominium' in sub:
        return 'Condo'
    # default any residential to SFR
    return 'SFR'

4.2 Aggregation

For each closed listing:

Determine ptype = classify_type(p)

Only keep where address.city == city_name (safety).

Group by ptype.

For each group:

Median Price: median sales.closePrice (fallback to listPrice).

Closed: count of listings.

DOM: average daysOnMarket.

Pseudo‑code:

from collections import defaultdict

by_type = defaultdict(list)
for p in closings:
    if p['address']['city'] != city_name:
        continue
    ptype = classify_type(p)
    by_type[ptype].append(p)

rows = []
for ptype in ['SFR', 'Condo', 'Townhome']:
    listings = by_type.get(ptype, [])
    if not listings:
        rows.append({'type': ptype, 'median': 0, 'closed': 0, 'dom': 0.0})
        continue

    prices = [(l.get('sales', {}).get('closePrice') or l['listPrice'])
              for l in listings]
    prices.sort()
    median_price = prices[len(prices)//2]

    dom_values = [l.get('daysOnMarket') or l.get('mls', {}).get('daysOnMarket', 0)
                  for l in listings]
    avg_dom = sum(dom_values) / len(dom_values) if dom_values else 0

    rows.append({
        'type': ptype,
        'median': median_price,
        'closed': len(listings),
        'dom': round(avg_dom, 1)
    })


Populate the table in SFR / Condo / Townhome order.

5. BY PRICE TIER table

Columns: Tier • Median • Closed • MOI (Entry, Move‑Up, Luxury).

We’ll define price tiers by price and then compute:

Median price (per tier)

Closed sales count (per tier)

Months of inventory (per tier)

5.1 Define the tiers

To keep it aligned with your existing price bands ranges, I’d recommend:

TIERS = [
    {'name': 'Entry',   'min': 0,        'max': 1_999_999},
    {'name': 'Move-Up', 'min': 2_000_000,'max': 2_999_999},
    {'name': 'Luxury',  'min': 3_000_000,'max': 999_999_999},
]


These boundaries play nicely with the price bands you already use in get_price_bands_data (under 2M, 2–3M, over 3M).

You can tune those numbers globally or per‑market later if needed.

5.2 Tier helpers
def tier_for_price(price):
    for t in TIERS:
        if t['min'] <= price <= t['max']:
            return t['name']
    return None

5.3 Aggregate closed & active per tier
from collections import defaultdict

# Closed by tier
closed_by_tier = defaultdict(list)
for p in closings:
    price = (p.get('sales', {}).get('closePrice') or p['listPrice'])
    tname = tier_for_price(price)
    if not tname:
        continue
    closed_by_tier[tname].append((p, price))

# Active by tier
active_by_tier = defaultdict(list)
for p in active:
    price = p['listPrice']
    tname = tier_for_price(price)
    if not tname:
        continue
    active_by_tier[tname].append(p)

5.4 Calculate Median, Closed, MOI per tier

For each tier in TIERS order:

tier_rows = []
for t in TIERS:
    name = t['name']
    closed_list = closed_by_tier.get(name, [])
    active_list = active_by_tier.get(name, [])

    # Median price from CLOSED sales in tier
    prices = [price for (_, price) in closed_list]
    prices.sort()
    median_price = prices[len(prices)//2] if prices else 0

    closed_count = len(closed_list)
    active_count = len(active_list)

    # Tier MOI: same formula but using tier counts
    if closed_count > 0:
        moi = active_count / (closed_count * (30 / period_days))
    else:
        moi = None  # or a large number / '—'

    tier_rows.append({
        'tier': name,
        'median': median_price,
        'closed': closed_count,
        'moi': round(moi, 1) if moi is not None else None
    })


Those values fill:

Entry row

Move‑Up row

Luxury row

6. How to explain this to Cursor / your team

If you want a succinct “dev spec” you can paste into Cursor, something like:

Market Snapshot – Data Model

Use 3 core queries:

get_closed_listings(city, lookback_days) → closed listings for status='Closed', mindate/maxdate on closeDate.

get_inventory_listings(city) → current active inventory status='Active'.

get_new_listings(city, lookback_days) → new listings status='Active' with listDate in window.

Plus a simple Pending query (status='Pending', same dates) for pending count.

Compute top KPIs from closings + active:

median_sale_price = median(closePrice)

closed_sales = len(closings)

avg_dom = avg(daysOnMarket)

moi = active_count / closed_count (scaled if window ≠ 30 days).

CORE indicators:

New Listings = len(new_listings)

Pending Sales = len(pendings) (or filter by contractDate)

Sale-to-List Ratio = avg (closePrice / listPrice * 100) for closings.

For each metric, also compute % change vs previous equal‑length window.

Property type table:

Classify each closed listing as SFR, Condo, Townhome using property.type + subType.

For each type: median closePrice, count closings, avg daysOnMarket.

Price tier table:

Define tiers by price: Entry (0–2M), Move-Up (2–3M), Luxury (3M+).

Bucket both closed and active listings into tiers.

For each tier:

median = median closed price;

closed = number of closings;

moi = active_count_tier / closed_count_tier (adjusted for window length).

If you’d like, next step I can turn this into actual Python helper functions (e.g. build_market_snapshot_metrics(city, lookback_days=30)) that mirror your existing get_*_listings functions so you can drop them straight into your reports repo.