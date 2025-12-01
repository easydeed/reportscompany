Totally—this is the perfect moment to lock these down so you’re not guessing every time.

Below is a “canonical queries” cheat‑sheet for the reports you’re using:

Market Snapshot

Listing Inventory by City

Closed Listings by City

Open Houses by City

All of these hit GET /properties on SimplyRETS, with different filters.

0. Shared conventions

Base URL

https://api.simplyrets.com/properties


Auth header – HTTP Basic with your key/secret (already in your config).

Recommended base params

COMMON = {
    # required if you ever have multiple MLS feeds
    "vendor": "crmls",     # or your MLS id

    # obey IDX rules; change if your MLS needs something else
    "idx": "address",      # or 'listing' / 'ignore'
}


✅ You can filter by city either with q="San Diego" (fuzzy keyword search) or more explicitly with cities="San Diego". The WordPress plugin uses cities for city filters, so I recommend that for tight “by City” reports. 
SimplyRETS Demo
+1

In the snippets below I’ll use cities; if your current code is using q, swap it in and keep the rest the same.

1) Market Snapshot (by City, last N days)

Goal
All activity (Active + Pending + Closed) for a city over a lookback window (e.g. last 30 days).

Params

params = {
    **COMMON,
    "cities": city,                      # e.g. "Irvine"
    "status": "Active,Pending,Closed",   # multiple statuses
    "mindate": start_date,               # 'YYYY-MM-DD'
    "maxdate": end_date,                 # 'YYYY-MM-DD'
    "limit": 1000,
    "offset": 0,
    "sort": "-listDate",                 # newest listings first
    # optional: only certain property types
    # "type": "RES,CND",                 # Residential + Condo
}


Example cURL

curl -u "$API_USER:$API_PASS" \
  "https://api.simplyrets.com/properties?cities=Irvine&status=Active,Pending,Closed&mindate=2025-11-01&maxdate=2025-12-01&limit=1000&offset=0&sort=-listDate"

2) Listing Inventory by City (Active inventory)

Goal
All currently active listings in a city, usually sorted by DOM (freshest first).

Params

params = {
    **COMMON,
    "cities": city,
    "status": "Active",      # inventory = on‑market
    "type": "RES,CND",       # tweak if you want more types
    "limit": 500,            # page size
    "offset": 0,
    "sort": "daysOnMarket",  # lowest DOM first
}


Pagination pattern

all_listings = []
offset = 0
limit = 500

while True:
    params["offset"] = offset
    params["limit"] = limit

    resp = requests.get(BASE_URL, params=params, headers=config.headers, timeout=30)
    resp.raise_for_status()
    batch = resp.json()

    if not batch:
        break

    all_listings.extend(batch)
    if len(batch) < limit:
        break

    offset += limit


Fields for your table

For each listing:

Property address → listing["address"]["full"]

City → listing["address"]["city"]

Beds → listing["property"]["bedrooms"]

Baths (total) → combine as needed:

baths = (
    (listing["property"].get("bathsFull") or 0)
    + 0.5 * (listing["property"].get("bathsHalf") or 0)
    + 0.75 * (listing["property"].get("bathsThreeQuarter") or 0)
)


Price → listing["listPrice"]

DOM → listing.get("daysOnMarket") or listing["mls"].get("daysOnMarket")

3) Closed Listings by City (recent sales)

Goal
Recently closed sales in a city in the last N days, sorted by most recent close date.

Params

params = {
    **COMMON,
    "cities": city,
    "status": "Closed",
    "mindate": start_date,    # lookback window
    "maxdate": end_date,
    "limit": 1000,
    "offset": 0,
    "sort": "-closeDate",     # most recent closings first
}


You can then compute metrics like total closed, median close price, avg DOM, etc., just like in your tech guide.

Table fields

Property address → address.full

City → address.city

Beds/Baths → same as inventory

Price → use sales.closePrice; fall back to listPrice if needed

DOM → daysOnMarket (top‑level or in mls)

4) Open Houses by City

Goal
Active listings in a city that have upcoming open houses in a given week (this week / next week, etc.).

There are two layers:

Filter the feed to Active listings in your date window.

Within the response, keep only listings that have openHouse data.

Params

params = {
    **COMMON,
    "cities": city,
    "status": "Active",
    "mindate": week_start,          # YYYY-MM-DD
    "maxdate": week_end,            # YYYY-MM-DD
    "limit": 500,
    "offset": 0,
    # Optional: extra hint to API; not all feeds use this,
    # but your guide notes `hasOpenHouse` as a feature flag.
    # "features": "hasOpenHouse",
}


Post‑filtering in code

resp = requests.get(BASE_URL, params=params, headers=config.headers, timeout=30)
resp.raise_for_status()
all_props = resp.json()

open_houses = []
for p in all_props:
    if p.get("openHouse") or (p.get("mls") and p["mls"].get("openHouse")):
        open_houses.append(p)


Then you can either:

Show only that city (if you passed cities=selectedCity), or

Pull the whole MLS and then group by address.city for a “Top open house cities” style report (your current open house builder does this).

Table fields (per listing)

Same structure:

Property address → address.full

City → address.city

Beds/Baths → from property

Price → listPrice

DOM → daysOnMarket

You can optionally add open house time from openHouse[] if you want a schedule column.

5) Price Bands (for your price‑tier tables)

Even though you didn’t call this out explicitly here, it feeds your price tier and property type tables, so it’s worth having the canonical query too.

Pattern: multiple queries per city, one per price band.

PRICE_BANDS = [
    {"name": "Under $500K",    "min": 0,       "max": 499_999},
    {"name": "$500K–$750K",    "min": 500_000, "max": 749_999},
    {"name": "$750K–$1M",      "min": 750_000, "max": 999_999},
    {"name": "$1M–$1.5M",      "min": 1_000_000, "max": 1_499_999},
    {"name": "$1.5M–$2M",      "min": 1_500_000, "max": 1_999_999},
    {"name": "$2M–$3M",        "min": 2_000_000, "max": 2_999_999},
    {"name": "Over $3M",       "min": 3_000_000, "max": 999_999_999},
]


For each band:

params = {
    **COMMON,
    "cities": city,
    "status": "Active",
    "minprice": band["min"],
    "maxprice": band["max"],
    "limit": 1000,
    "offset": 0,
}


Then compute counts, median price, avg DOM, etc., as in your guide.

6) Quick “am I calling it right?” checklist

If a report comes back empty or weird:

Confirm the city filter

Try cities=CityName first.

If you use q, remember it’s a fuzzy search (MLS #, address, city, zip, etc.).

Check status

Inventory → Active

Closed → Closed

Market snapshot → Active,Pending,Closed

Open Houses → Active + openHouse presence

Date range

All dates as YYYY-MM-DD.

For “last N days”, compute mindate / maxdate exactly like in the guide (now minus N days).

Limit / offset

Max 500 per request; loop with offset until you get a short page.

IDX / vendor

Make sure vendor=crmls (or your board) and an idx value that matches your MLS rules, especially for social / public reports.