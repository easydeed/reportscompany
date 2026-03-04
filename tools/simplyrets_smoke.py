#!/usr/bin/env python3
"""
SimplyRETS Smoke Test CLI
=========================
Validates SimplyRETS connectivity, available metadata, and query correctness
WITHOUT touching the UI. All calls go directly to api.simplyrets.com.

Usage:
    python tools/simplyrets_smoke.py options
    python tools/simplyrets_smoke.py market --city "Anaheim" --status Active --limit 5
    python tools/simplyrets_smoke.py market --city "Anaheim" --status Active --limit 5 --debug
    python tools/simplyrets_smoke.py comps --city "Anaheim" --postal "92805" \
        --beds 3 --baths 2 --sqft 1800 --status Closed --limit 10 --debug

Environment variables (set before running):
    SIMPLYRETS_USERNAME   (default: simplyrets  — demo account)
    SIMPLYRETS_PASSWORD   (default: simplyrets  — demo account)
    SIMPLYRETS_BASE_URL   (default: https://api.simplyrets.com)
    SIMPLYRETS_VENDOR     (optional MLS vendor/feed ID)

Exit codes:
    0 — success (results found)
    1 — error (HTTP failure, 0 results, or misconfiguration)
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Standard library only — no project imports required
try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("ERROR: 'requests' package not installed. Run: pip install requests")
    sys.exit(1)

# --- Configuration ------------------------------------------------------------

BASE_URL  = os.environ.get("SIMPLYRETS_BASE_URL", "https://api.simplyrets.com").rstrip("/")
USERNAME  = os.environ.get("SIMPLYRETS_USERNAME", "simplyrets")
PASSWORD  = os.environ.get("SIMPLYRETS_PASSWORD", "simplyrets")
VENDOR    = os.environ.get("SIMPLYRETS_VENDOR", "")
AUTH      = HTTPBasicAuth(USERNAME, PASSWORD)
TIMEOUT   = (10, 30)   # (connect, read)

IS_DEMO = USERNAME.lower() == "simplyrets"

# --- Helpers -----------------------------------------------------------------

def _inject_vendor(params: Dict) -> Dict:
    """Add vendor param if SIMPLYRETS_VENDOR is set."""
    if VENDOR and "vendor" not in params:
        return {**params, "vendor": VENDOR}
    return params


def _safe_url(params: Dict) -> str:
    """Build display URL masking credentials."""
    import urllib.parse
    qs = urllib.parse.urlencode(params)
    return f"GET {BASE_URL}/properties?{qs}"


def _print_section(title: str):
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")


def _check_response(resp: "requests.Response", endpoint: str, debug: bool = False):
    """Print response details and raise on error."""
    if debug:
        print(f"  -> HTTP {resp.status_code}  [{len(resp.content)} bytes]")
    if resp.status_code == 401:
        print(f"\n[ERROR]  401 Unauthorized — Check env vars:")
        print(f"     SIMPLYRETS_USERNAME = {USERNAME}")
        print(f"     SIMPLYRETS_PASSWORD = {'*' * len(PASSWORD)} ({len(PASSWORD)} chars)")
        if VENDOR:
            print(f"     SIMPLYRETS_VENDOR   = {VENDOR}")
        sys.exit(1)
    if resp.status_code == 403:
        print(f"\n[ERROR]  403 Forbidden — Your credentials may not have access to {endpoint}")
        if VENDOR:
            print(f"     Vendor: {VENDOR}")
        sys.exit(1)
    if resp.status_code == 429:
        print(f"\n[WARN]   429 Rate Limited — SimplyRETS is throttling requests. Wait and retry.")
        sys.exit(1)
    if not resp.ok:
        print(f"\n[ERROR]  HTTP {resp.status_code} from {endpoint}")
        print(f"     Body: {resp.text[:500]}")
        sys.exit(1)


# --- Command: options ---------------------------------------------------------

def _fetch_options_meta(debug: bool = False):
    """Fetch raw OPTIONS /properties response. Returns (meta_dict, raw_text)."""
    params = _inject_vendor({})
    url = f"{BASE_URL}/properties"
    if debug:
        print(f"\n  Request: OPTIONS {url}  params={params}")
    try:
        resp = requests.options(url, params=params, auth=AUTH, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        print(f"\n[ERROR]  Connection error: {e}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"\n[ERROR]  Timeout connecting to {BASE_URL}")
        sys.exit(1)
    _check_response(resp, "OPTIONS /properties", debug)
    if not resp.text.strip():
        return None, ""
    try:
        return resp.json(), resp.text
    except ValueError:
        return None, resp.text


def parse_options_meta(meta: dict):
    """
    Parse OPTIONS response into (statuses, types, subtypes, cities).
    Handles both flat and fields-nested shapes.
    """
    fields = meta.get("fields") or meta
    statuses = (fields.get("statuses") or fields.get("status") or
                meta.get("statuses") or meta.get("status") or [])
    types    = (fields.get("types") or fields.get("type") or
                meta.get("types") or meta.get("type") or [])
    subtypes = (fields.get("subtypes") or fields.get("subtype") or
                meta.get("subtypes") or meta.get("subtype") or [])
    cities   = (fields.get("cities") or meta.get("cities") or [])
    return statuses, types, subtypes, cities


def cmd_options(debug: bool = False, raw: bool = False):
    """
    OPTIONS /properties — discover what the feed supports.
    --raw: also prints top-level keys, nested paths, and first 25 values each.
    """
    _print_section("SimplyRETS OPTIONS /properties")
    print(f"  Account : {USERNAME} ({'demo' if IS_DEMO else 'production'})")
    print(f"  Vendor  : {VENDOR or '(none)'}")
    print(f"  Base URL: {BASE_URL}")

    meta, raw_text = _fetch_options_meta(debug=debug)

    if meta is None:
        if not raw_text.strip():
            print("\n[WARN]   OPTIONS returned empty body (HTTP 204 or no content).")
        else:
            print(f"\n[WARN]   OPTIONS response is not valid JSON: {raw_text[:300]}")
        return

    # --raw: dump schema structure
    if raw:
        print(f"\n  Top-level keys ({len(meta)}): {sorted(meta.keys())}")
        fields_obj = meta.get("fields")
        if fields_obj and isinstance(fields_obj, dict):
            print(f"  'fields' sub-keys ({len(fields_obj)}): {sorted(fields_obj.keys())}")
            print(f"\n  Path analysis:")
            for key in sorted(fields_obj.keys()):
                val = fields_obj[key]
                if isinstance(val, list):
                    print(f"    fields.{key}: list({len(val)})  first 5: {val[:5]}")
                else:
                    print(f"    fields.{key}: {type(val).__name__} = {repr(val)[:80]}")
        else:
            print(f"  No 'fields' nesting — flat structure")
            for key in sorted(meta.keys()):
                val = meta[key]
                if isinstance(val, list):
                    print(f"    {key}: list({len(val)})  first 5: {val[:5]}")

    statuses, types, subtypes, cities = parse_options_meta(meta)

    # -- Print statuses
    print(f"\n  Available statuses ({len(statuses)}):")
    for s in (statuses[:25] if raw else statuses[:20]):
        print(f"    - {s}")

    # -- Print types
    print(f"\n  Available property types ({len(types)}):")
    for t in (types[:25] if raw else types[:20]):
        print(f"    - {t}")

    # -- Print subtypes
    if subtypes:
        print(f"\n  Available subtypes ({len(subtypes)}):")
        for st in (subtypes[:25] if raw else subtypes[:15]):
            print(f"    - {st}")

    # -- Print cities
    print(f"\n  Available cities: {len(cities)} total")
    if cities:
        n = 25 if raw else 20
        print(f"  First {min(n, len(cities))}:")
        for c in cities[:n]:
            print(f"    - {c}")

    # -- Feed metadata
    if meta.get("lastUpdate"):
        print(f"\n  Feed last updated : {meta['lastUpdate']}")
    if meta.get("expires"):
        print(f"  Metadata expires  : {meta['expires']}")

    if raw:
        # Show field path summary for parser
        fields_obj = meta.get("fields") or {}
        status_path  = "fields.status"  if "status"  in fields_obj else "status"
        type_path    = "fields.type"    if "type"    in fields_obj else "type"
        cities_path  = "fields.cities"  if "cities"  in fields_obj else "cities"
        subtype_path = "fields.subtype" if "subtype" in fields_obj else "subtype"
        print(f"\n  Parser paths confirmed:")
        print(f"    statuses  -> {status_path}  ({len(statuses)} values)")
        print(f"    types     -> {type_path}    ({len(types)} values)")
        print(f"    subtypes  -> {subtype_path} ({len(subtypes)} values)")
        print(f"    cities    -> {cities_path}  ({len(cities)} values)")

    print(f"\n[OK]  OPTIONS completed successfully")


# --- Command: market ----------------------------------------------------------

def cmd_market(city: str, status: str = "Active", limit: int = 5, debug: bool = False):
    """
    GET /properties with cities=<city> and status filter.
    Verifies that market report city queries return results.
    """
    _print_section(f"Market Query — city={city!r}, status={status}, limit={limit}")
    print(f"  Account : {USERNAME} ({'demo' if IS_DEMO else 'production'})")
    print(f"  Vendor  : {VENDOR or '(none)'}")

    if IS_DEMO:
        print(f"\n  [WARN]   Demo credentials detected (simplyrets/simplyrets).")
        print(f"       Demo feed is Houston-only. 'cities' param may not be respected.")
        print(f"       Trying with cities= first, then falling back to q= if 0 results.\n")

    # Try 1: cities= (deterministic, preferred)
    city_param_used = "cities"
    params = _inject_vendor({
        "cities": city,
        "status": status,
        "limit": limit,
    })

    if debug:
        print(f"  Request 1 (cities=): {_safe_url(params)}")

    try:
        resp = requests.get(f"{BASE_URL}/properties", params=params, auth=AUTH, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        print(f"\n[ERROR]  Connection error: {e}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"\n[ERROR]  Timeout connecting to {BASE_URL}")
        sys.exit(1)

    _check_response(resp, "GET /properties", debug)

    data = resp.json()
    count = len(data) if isinstance(data, list) else 0

    if debug:
        print(f"  -> HTTP {resp.status_code}, {count} results")

    # Fallback to q= if cities= returned nothing (demo feed / older accounts)
    if count == 0 and IS_DEMO:
        city_param_used = "q"
        params2 = _inject_vendor({"q": city, "status": status, "limit": limit})
        if debug:
            print(f"\n  Fallback (q=): {_safe_url(params2)}")

        resp2 = requests.get(f"{BASE_URL}/properties", params=params2, auth=AUTH, timeout=TIMEOUT)
        _check_response(resp2, "GET /properties (fallback q=)", debug)
        data = resp2.json()
        count = len(data) if isinstance(data, list) else 0
        if debug:
            print(f"  -> Fallback HTTP {resp2.status_code}, {count} results")

    # -- Print results --------------------------------------------------------
    print(f"\n  City param used : {city_param_used}=")
    print(f"  Results returned: {count}")

    if count == 0:
        print(f"\n[WARN]   0 results for city={city!r}, status={status}.")
        if not IS_DEMO:
            print(f"     Suggestion: run 'options' command to see available cities.")
        else:
            print(f"     Demo feed is Houston-only. Try --city 'Houston' or a Houston ZIP.")
        sys.exit(1)

    # Print 3 sample properties
    samples = data[:3]
    print(f"\n  Sample addresses (first {len(samples)}):")
    for i, prop in enumerate(samples, 1):
        addr = prop.get("address", {})
        mls_id = prop.get("mlsId", "?")
        full   = addr.get("full", "N/A")
        city_v = addr.get("city", "?")
        price  = prop.get("listPrice") or prop.get("closePrice") or "?"
        status_v = (prop.get("mls") or {}).get("status", "?")
        print(f"    [{i}] MLS#{mls_id}  {full}, {city_v}  ${price:,}  [{status_v}]"
              if isinstance(price, int) else
              f"    [{i}] MLS#{mls_id}  {full}, {city_v}  ${price}  [{status_v}]")

    # Show available city_param field names for reference
    if debug and data:
        prop0 = data[0]
        print(f"\n  Debug — Sample raw keys: {list(prop0.keys())[:10]}")
        addr0 = prop0.get("address", {})
        print(f"  Debug — Address keys: {list(addr0.keys())}")

    print(f"\n[OK]  Market query succeeded: {count} results using {city_param_used}=")


# --- Command: comps ----------------------------------------------------------

def cmd_comps(
    city: Optional[str],
    postal: Optional[str],
    beds: int,
    baths: float,
    sqft: int,
    status: str = "Closed",
    limit: int = 10,
    debug: bool = False,
):
    """
    GET /properties with comps-style filters and fallback ladder.
    Simulates what property reports do when fetching comparable sales.
    """
    _print_section(
        f"Comps Query — city={city!r}, postal={postal!r}, "
        f"beds={beds}, baths={baths}, sqft={sqft}"
    )
    print(f"  Account : {USERNAME} ({'demo' if IS_DEMO else 'production'})")
    print(f"  Vendor  : {VENDOR or '(none)'}")

    FALLBACK_MIN = max(3, limit // 3)

    # Ladder: (label, sqft_variance, extra_beds, include_subtype, use_city)
    LADDER: List[Tuple[str, Optional[float], int, bool, bool]] = [
        ("L0:strict",             0.20, 0, True,  True),
        ("L1:no-subtype",         0.20, 0, False, True),
        ("L2:sqft±30%",           0.30, 0, False, True),
        ("L3:sqft±40%,beds±1",    0.40, 1, False, True),
        ("L4:sqft±50%,beds±2",    0.50, 2, False, True),
        ("L5:no-sqft,no-subtype", None, 2, False, True),
    ]

    def _build_params(sqft_var: Optional[float], extra_beds: int,
                      incl_sub: bool, use_city: bool) -> Dict:
        p: Dict[str, Any] = {
            "type": "residential",   # valid SimplyRETS type value
            "status": status,
            "limit": limit * 4,
        }
        if postal:
            p["postalCodes"] = postal
        if city and use_city:
            p["cities"] = city
        if sqft_var is not None:
            p["minarea"] = int(sqft * (1 - sqft_var))
            p["maxarea"] = int(sqft * (1 + sqft_var))
        p["minbeds"] = max(1, beds - 1 - extra_beds)
        p["maxbeds"] = beds + 1 + extra_beds
        if extra_beds == 0:
            p["minbaths"] = max(1, int(baths) - 1)
            p["maxbaths"] = int(baths) + 1
        if incl_sub:
            p["subtype"] = "SingleFamilyResidence"
        return _inject_vendor(p)

    # Run fallback ladder
    result_data: List[Dict] = []
    level_used = "none"

    for label, sqft_var, extra_beds, incl_sub, use_city in LADDER:
        params = _build_params(sqft_var, extra_beds, incl_sub, use_city)

        if debug:
            print(f"\n  Ladder {label}: {_safe_url(params)}")
        else:
            print(f"  Trying {label}…", end=" ", flush=True)

        try:
            resp = requests.get(
                f"{BASE_URL}/properties", params=params, auth=AUTH, timeout=TIMEOUT
            )
        except requests.exceptions.Timeout:
            print(f"TIMEOUT")
            continue

        _check_response(resp, f"GET /properties ({label})", debug)
        data = resp.json()
        count = len(data) if isinstance(data, list) else 0

        if debug:
            print(f"  -> {count} results")
        else:
            print(f"{count} results")

        if count >= FALLBACK_MIN:
            result_data = data
            level_used = label
            break
        elif count > 0 and not result_data:
            # Keep best partial result
            result_data = data
            level_used = label

    total = len(result_data)
    print(f"\n  Ladder level used : {level_used}")
    print(f"  Total results     : {total}")

    if total == 0:
        print(f"\n[ERROR]  0 results after exhausting fallback ladder.")
        print(f"     Suggestions:")
        print(f"       1. Run 'options' to see available cities/types")
        print(f"       2. Try a different --postal or --city")
        if IS_DEMO:
            print(f"       3. Demo feed is Houston-only; try postal=77001 or city=Houston")
        sys.exit(1)

    # Print sample results
    samples = result_data[:3]
    print(f"\n  Sample comps (first {len(samples)}):")
    for i, prop in enumerate(samples, 1):
        addr    = prop.get("address", {})
        mls_id  = prop.get("mlsId", "?")
        full    = addr.get("full", "N/A")
        price   = prop.get("closePrice") or prop.get("listPrice") or "?"
        prop_d  = prop.get("property", {})
        p_beds  = prop_d.get("bedrooms", "?")
        p_baths = prop_d.get("bathsFull", "?")
        p_sqft  = prop_d.get("area", "?")
        subtype = prop_d.get("subType", "?")
        status_v = (prop.get("mls") or {}).get("status", "?")
        print(f"    [{i}] MLS#{mls_id}  {full}")
        print(f"         ${price:,}  {p_beds}bd/{p_baths}ba  {p_sqft}sqft  subtype={subtype}  [{status_v}]"
              if isinstance(price, int) else
              f"         ${price}  {p_beds}bd/{p_baths}ba  {p_sqft}sqft  subtype={subtype}  [{status_v}]")

    print(f"\n[OK]  Comps query succeeded at {level_used}: {total} results")


# --- Command: cities-check ---------------------------------------------------

def cmd_cities_check(cities_str: str, limit: int = 3, debug: bool = False):
    """
    Health-check multiple cities for both Active and Closed listings.
    Outputs: count, mlsId, address, listPrice/closePrice, subType, photo count.
    """
    cities_list = [c.strip() for c in cities_str.split(",") if c.strip()]
    _print_section(f"Cities Health Check — {len(cities_list)} cities, limit={limit}")
    print(f"  Cities  : {cities_list}")
    print(f"  Account : {USERNAME} ({'demo' if IS_DEMO else 'production'})")

    results = []
    for city in cities_list:
        city_row = {"city": city, "active": [], "closed": []}

        for status in ("Active", "Closed"):
            params = _inject_vendor({
                "cities": city,
                "status": status,
                "limit": limit,
            })
            if debug:
                print(f"\n  {city} {status}: {_safe_url(params)}")
            else:
                print(f"\n  Querying {city!r} [{status}]…", end=" ", flush=True)

            try:
                resp = requests.get(
                    f"{BASE_URL}/properties", params=params,
                    auth=AUTH, timeout=TIMEOUT
                )
                _check_response(resp, f"GET /properties ({city} {status})", debug)
                data = resp.json()
            except SystemExit:
                data = []

            count = len(data) if isinstance(data, list) else 0
            if not debug:
                print(f"{count} results")

            samples = []
            for prop in data[:limit]:
                addr   = prop.get("address", {})
                prop_d = prop.get("property", {})
                mls_d  = prop.get("mls", {}) or {}
                sales  = prop.get("sales") or {}
                photos = prop.get("photos") or []
                assoc  = prop.get("association") or {}

                sample = {
                    "mlsId":         prop.get("mlsId"),
                    "address":       addr.get("full", "?"),
                    "city":          addr.get("city", "?"),
                    "postalCode":    addr.get("postalCode"),
                    "listPrice":     prop.get("listPrice"),
                    "originalListPrice": prop.get("originalListPrice"),
                    "status":        mls_d.get("status"),
                    "dom":           mls_d.get("daysOnMarket"),
                    "subType":       prop_d.get("subType"),
                    "beds":          prop_d.get("bedrooms"),
                    "baths":         prop_d.get("bathsFull"),
                    "sqft":          prop_d.get("area"),
                    "lotSqft":       prop_d.get("lotSizeArea"),
                    "yearBuilt":     prop_d.get("yearBuilt"),
                    "hoaFee":        assoc.get("fee"),
                    "photoCount":    len(photos),
                    "schoolDistrict": (prop.get("school") or {}).get("district"),
                }
                if status == "Closed":
                    sample["closePrice"]    = sales.get("closePrice")
                    sample["closeDate"]     = sales.get("closeDate")
                    sample["contractDate"]  = sales.get("contractDate")
                    sample["contractDatePresent"] = bool(sales.get("contractDate"))
                samples.append(sample)

            city_row[status.lower()] = {"count": count, "samples": samples}

        results.append(city_row)

    # Print formatted report
    print()
    print("=" * 70)
    print("CITIES HEALTH CHECK RESULTS")
    print("=" * 70)
    for row in results:
        city = row["city"]
        print(f"\n--- {city} ---")

        for status_key, label in [("active", "ACTIVE"), ("closed", "CLOSED")]:
            info = row.get(status_key, {})
            count = info.get("count", 0)
            samples = info.get("samples", [])
            print(f"\n  [{label}] {count} results returned (limit={limit})")
            for i, s in enumerate(samples, 1):
                price_label = "closePrice" if status_key == "closed" else "listPrice"
                price_val   = s.get("closePrice") or s.get("listPrice")
                price_str   = f"${price_val:,}" if isinstance(price_val, int) else str(price_val)
                cut_flag    = ""
                if status_key == "active":
                    orig = s.get("originalListPrice") or 0
                    curr = s.get("listPrice") or 0
                    if orig and curr and orig > curr:
                        cut_flag = f"  [PRICE CUT: -${orig - curr:,}]"

                print(f"    [{i}] mlsId={s['mlsId']}  {s['address']}, {s['city']}  {price_str}{cut_flag}")
                print(f"         subType={s['subType']}  {s['beds']}bd/{s['baths']}ba  "
                      f"{s['sqft']}sqft  lot={s['lotSqft']}sqft  yr={s['yearBuilt']}")
                print(f"         DOM={s['dom']}  HOA=${s.get('hoaFee', '?')}  photos={s['photoCount']}  "
                      f"school={s.get('schoolDistrict', '?')}")
                if status_key == "closed":
                    print(f"         closeDate={s.get('closeDate')}  "
                          f"contractDate={'PRESENT' if s.get('contractDatePresent') else 'NULL'}  "
                          f"closePrice=${s.get('closePrice', '?'):,}" if isinstance(s.get('closePrice'), int)
                          else f"         closeDate={s.get('closeDate')}  "
                          f"contractDate={'PRESENT' if s.get('contractDatePresent') else 'NULL'}")

    print(f"\n[OK]  Cities check complete ({len(results)} cities)")


# --- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="simplyrets_smoke",
        description="SimplyRETS CLI smoke test — validates API connectivity and query params",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/simplyrets_smoke.py options
  python tools/simplyrets_smoke.py market --city "Anaheim" --status Active --limit 5
  python tools/simplyrets_smoke.py market --city "Houston" --status Active --limit 5 --debug
  python tools/simplyrets_smoke.py comps --city "Anaheim" --postal "92805" \\
      --beds 3 --baths 2 --sqft 1800 --status Closed --limit 10 --debug

Environment vars:
  SIMPLYRETS_USERNAME  (default: simplyrets — demo)
  SIMPLYRETS_PASSWORD  (default: simplyrets — demo)
  SIMPLYRETS_BASE_URL  (default: https://api.simplyrets.com)
  SIMPLYRETS_VENDOR    (optional)
        """
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # -- options --------------------------------------------------------------
    p_opts = sub.add_parser("options", help="Run OPTIONS /properties to see feed metadata")
    p_opts.add_argument("--debug", action="store_true")
    p_opts.add_argument("--raw", action="store_true",
                        help="Print raw top-level keys, nested paths, and first 25 values")

    # -- market ---------------------------------------------------------------
    p_mkt = sub.add_parser("market", help="Fetch market listings for a city")
    p_mkt.add_argument("--city",   required=True, help="City name (e.g., 'Anaheim')")
    p_mkt.add_argument("--status", default="Active",
                       choices=["Active", "Closed", "Pending", "ActiveUnderContract"],
                       help="Listing status filter")
    p_mkt.add_argument("--limit",  type=int, default=5, help="Max results to return")
    p_mkt.add_argument("--debug",  action="store_true", help="Print raw request/response details")

    # -- cities-check ---------------------------------------------------------
    p_cc = sub.add_parser("cities-check",
                           help="Health-check multiple cities for Active+Closed listings")
    p_cc.add_argument("--cities", required=True,
                      help="Comma-separated city names, e.g. 'Downey,La Verne,San Diego'")
    p_cc.add_argument("--limit", type=int, default=3,
                      help="Max results per city per status (default 3)")
    p_cc.add_argument("--debug", action="store_true")

    # -- comps ----------------------------------------------------------------
    p_cmp = sub.add_parser("comps", help="Fetch comparable sales with fallback ladder")
    p_cmp.add_argument("--city",   default=None, help="City name")
    p_cmp.add_argument("--postal", default=None, help="ZIP/postal code")
    p_cmp.add_argument("--beds",   type=int, required=True, help="Subject property bedrooms")
    p_cmp.add_argument("--baths",  type=float, required=True, help="Subject property bathrooms")
    p_cmp.add_argument("--sqft",   type=int, required=True, help="Subject property sqft")
    p_cmp.add_argument("--status", default="Closed",
                       choices=["Closed", "Active", "Pending"],
                       help="Listing status filter")
    p_cmp.add_argument("--limit",  type=int, default=10, help="Target number of results")
    p_cmp.add_argument("--debug",  action="store_true", help="Print raw request/response details")

    args = parser.parse_args()

    print(f"\nSimplyRETS Smoke Test")
    print(f"  Username : {USERNAME}")
    print(f"  Feed     : {'DEMO (Houston-only)' if IS_DEMO else 'PRODUCTION'}")
    print(f"  Vendor   : {VENDOR or '(none)'}")
    print(f"  Base URL : {BASE_URL}")

    if args.cmd == "options":
        cmd_options(debug=args.debug, raw=getattr(args, "raw", False))
    elif args.cmd == "cities-check":
        cmd_cities_check(args.cities, args.limit, args.debug)
    elif args.cmd == "market":
        cmd_market(args.city, args.status, args.limit, args.debug)
    elif args.cmd == "comps":
        if not args.city and not args.postal:
            parser.error("comps requires at least --city or --postal")
        cmd_comps(
            city=args.city,
            postal=args.postal,
            beds=args.beds,
            baths=args.baths,
            sqft=args.sqft,
            status=args.status,
            limit=args.limit,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()
