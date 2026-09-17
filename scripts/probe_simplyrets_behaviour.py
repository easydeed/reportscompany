#!/usr/bin/env python3
"""
Ask the SimplyRETS feed three questions this repository has been guessing at.

READ ONLY. Six GET requests to /properties. No writes, no state, nothing
cached. Safe to run against production at any time.

    export SIMPLYRETS_USERNAME=...    # the production values
    export SIMPLYRETS_PASSWORD=...
    python scripts/probe_simplyrets_behaviour.py

WHY THIS EXISTS AS A SCRIPT
---------------------------
Three vendor behaviours were measured against the PUBLIC DEMO FEED and three
defects filed on them (D-074, D-075, D-076). This repository already knows the
demo and production feeds differ — `IS_DEMO`, `ALLOW_CITY_SEARCH` and
`ALLOW_SORTING` exist for exactly that reason — so those measurements settle
nothing on their own. §0.6 rule 1: a sample shows what the code *can* do, not
what it *does*.

The most consequential answer is D-074's. `market_trends.py` believes there is
no close-date filter and works around it with a 210-day list-date window, which
excludes homes listed more than seven months ago and sold recently. Long-DOM
listings are exactly the ones that take that long, so the loss is not random:
it removes real sales from the denominator, and months-of-supply comes out too
HIGH, never too low. High supply flips the market-condition badge to
buyer's-market and generates copy about homes taking longer to sell. **A seller
reading that page prices lower than the market warrants.** That has been
shipping on the property report.

REFUSES TO RUN AGAINST THE DEMO FEED without --allow-demo, because a demo
answer pasted into a production discussion is the whole mistake this is here to
avoid.
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

BASE = os.getenv("SIMPLYRETS_BASE_URL", "https://api.simplyrets.com")
DEMO_USER = "simplyrets"
TIMEOUT = 30


def _get(auth, query, label):
    """One GET. Returns (rows, status_counts, seconds) or None on failure."""
    url = f"{BASE}/properties?{query}"
    req = urllib.request.Request(
        url, headers={"Authorization": auth, "Accept": "application/json"}
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:120].decode("utf-8", "replace")
        print(f"  {label:44s} HTTP {exc.code}  {detail}")
        return None
    except Exception as exc:  # noqa: BLE001 — a probe reports, it does not raise
        print(f"  {label:44s} {type(exc).__name__}: {exc}")
        return None
    elapsed = time.time() - started
    counts = Counter((row.get("mls") or {}).get("status") for row in body)
    print(f"  {label:44s} {len(body):5d} rows  {elapsed:5.2f}s  {dict(counts)}")
    return body, counts, elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-demo",
        action="store_true",
        help="run even though the credentials are the public demo ones",
    )
    args = parser.parse_args()

    user = os.getenv("SIMPLYRETS_USERNAME", "")
    password = os.getenv("SIMPLYRETS_PASSWORD", "")
    if not user or not password:
        sys.exit(
            "SIMPLYRETS_USERNAME and SIMPLYRETS_PASSWORD must be set.\n"
            "Use the PRODUCTION values — demo answers settle nothing."
        )
    if user.lower() == DEMO_USER and not args.allow_demo:
        sys.exit(
            "These are the public demo credentials.\n"
            "Every finding this probe exists to confirm was already measured "
            "against the demo feed; re-measuring it there answers nothing.\n"
            "Set the production values, or pass --allow-demo to see the demo "
            "numbers again."
        )

    auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
    print(f"Feed: {BASE}   user: {user}   "
          f"({'DEMO' if user.lower() == DEMO_USER else 'PRODUCTION'})")
    print("Six GETs, read only.\n")

    verdicts = {}

    # ── 1. multi-value status (D-076) ───────────────────────────────────────
    print("1. Does a comma-separated status return more than one status?")
    active = _get(auth, "status=Active&limit=500", "status=Active")
    comma = _get(auth, "status=Active%2CClosed&limit=500", "status=Active,Closed  (comma)")
    repeated = _get(auth, "status=Active&status=Closed&limit=500", "status=Active&status=Closed")
    if comma and repeated:
        comma_kinds = {k for k in comma[1] if k}
        repeated_kinds = {k for k in repeated[1] if k}
        if len(comma_kinds) < len(repeated_kinds):
            verdicts["D-076"] = (
                "CONFIRMED — the comma form silently drops values "
                f"(comma returned {sorted(comma_kinds)}, repeated returned "
                f"{sorted(repeated_kinds)}). The fix already shipped is correct."
            )
        elif comma_kinds == repeated_kinds:
            verdicts["D-076"] = (
                "NOT REPRODUCED on this feed — both forms returned "
                f"{sorted(comma_kinds)}. The shipped fix is still correct "
                "(repeated parameters are the standard encoding) but the "
                "defect is demo-only; close it as closed-not-live."
            )
    print()

    # ── 2. minclosedate (D-074) ─────────────────────────────────────────────
    print("2. Does minclosedate filter? (this is the one with a shipping consequence)")
    closed_all = _get(auth, "status=Closed&limit=500", "status=Closed  (baseline)")
    closed_future = _get(auth, "status=Closed&minclosedate=2030-01-01&limit=500",
                         "  + minclosedate=2030-01-01")
    if closed_all and closed_future:
        if len(closed_future[0]) == 0 and len(closed_all[0]) > 0:
            verdicts["D-074"] = (
                "CONFIRMED — minclosedate works. market_trends.py's 210-day "
                "listDate workaround is unnecessary AND lossy: it drops "
                "long-DOM recent sales, deflating the sales rate and inflating "
                "months of supply. Remove minlistdate and filter on close date. "
                "LIVE on the property report."
            )
        elif len(closed_future[0]) == len(closed_all[0]):
            verdicts["D-074"] = (
                "NOT CONFIRMED — minclosedate is accepted and ignored. The "
                "210-day workaround is the right design; what remains is "
                "whether 210 days is the right window, since it truncates the "
                "tail either way. Re-scope the entry."
            )
        else:
            verdicts["D-074"] = (
                f"AMBIGUOUS — a future minclosedate returned "
                f"{len(closed_future[0])} of {len(closed_all[0])} rows, which "
                "is neither 'filters' nor 'ignored'. Paste the output."
            )
    print()

    # ── 3. mindate (D-075) ──────────────────────────────────────────────────
    print("3. Does mindate do anything?")
    mindate_future = _get(auth, "status=Closed&mindate=2030-01-01&limit=500",
                          "  + mindate=2030-01-01")
    if closed_all and mindate_future:
        if len(mindate_future[0]) == len(closed_all[0]):
            verdicts["D-075"] = (
                "CONFIRMED — mindate is accepted and ignored, silently. The "
                "report builders' client-side filtering is load-bearing, not "
                "belt-and-braces. Impact is nil today; the trap is for whoever "
                "trusts the parameter next."
            )
        elif len(mindate_future[0]) == 0:
            verdicts["D-075"] = (
                "NOT REPRODUCED — mindate filters on this feed. Demo-only "
                "quirk; close as closed-not-live."
            )
    print()

    # ── verdicts ────────────────────────────────────────────────────────────
    print("=" * 72)
    for defect in ("D-074", "D-075", "D-076"):
        print(f"\n{defect}: {verdicts.get(defect, 'INCONCLUSIVE — a request failed above')}")
    print("\n" + "=" * 72)
    print("Paste this whole output back. The wording of each verdict is what "
          "goes on the defect entry.")
    if active:
        print(f"\nIncidentally: {len(active[0])} active listings came back in "
              f"{active[2]:.2f}s. If that number is at the 500 page limit, say "
              f"so — the inventory report's months-of-supply numerator now "
              f"needs a city's WHOLE active inventory and refuses to publish a "
              f"figure when its fetch truncates (see D-056).")


if __name__ == "__main__":
    main()
