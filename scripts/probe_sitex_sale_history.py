#!/usr/bin/env python3
"""Does SiteX carry a last-sale price and date for the subject? (D-118)

WHY THIS CANNOT BE ANSWERED FROM THE REPOSITORY
-----------------------------------------------
Jerry, 2026-09-29: the subject's price row should be its LAST ACTUAL SALE, and
where the feed does not carry one the row shows nothing rather than a
substitute. Today it shows the county's Prop 13 assessment (D-118).

Three things are known from the code and none of them answers the question:

  * `SiteXClient._parse_response` extracts address, owner, legal, tax and
    characteristics. It reads NO sale-history field.
  * `PropertyData` has no slot for one, so even a field present in the payload
    would be dropped at the boundary.
  * Every `.json`, `.py` and `.md` in the repository was searched for
    `PropertyProfile`. The only hit is the parser itself — **no real SiteX
    response has ever been captured here.**

So "SiteX does not give us last-sale data" and "SiteX gives it to us and we
throw it away" are indistinguishable from inside the repository, and they lead
to completely different tickets. One real lookup separates them. §0.6: ask
what writes this, and do not reason about what its absence proves.

WHAT IT DOES
------------
One address lookup. It prints the KEY NAMES under `Feed.PropertyProfile` and
the contents of any section whose name suggests sale, transfer or deed
history. It does not print owner names, and it truncates every value, because
the output is meant to be pasted into a ticket.

READ ONLY. One GET for a token, one for the property. No writes.

    SITEX_CLIENT_ID=... SITEX_CLIENT_SECRET=... SITEX_FEED_ID=... \
    SITEX_BASE_URL=... python3 scripts/probe_sitex_sale_history.py \
        "1358 5th Street" "La Verne, CA 91750"
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

#: Section names worth opening if they appear. Matched case-insensitively as
#: substrings, because the exact spelling is the thing being discovered — a
#: fixed list of expected keys would report "not found" for a field named
#: something adjacent, which is the failure this probe exists to avoid.
SALE_HINTS = ("sale", "transfer", "deed", "transaction", "market", "history",
              "mortgage", "ownership")

#: Never printed, at any depth. The probe goes in a ticket.
REDACT = ("owner", "name", "mailing")


def _redacted(key: str) -> bool:
    return any(r in key.lower() for r in REDACT)


def _dump(obj, indent="    ", depth=0):
    if depth > 2:
        print(f"{indent}…")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _redacted(k):
                print(f"{indent}{k}: <redacted>")
            elif isinstance(v, (dict, list)):
                print(f"{indent}{k}:")
                _dump(v, indent + "  ", depth + 1)
            else:
                print(f"{indent}{k}: {str(v)[:60]}")
    elif isinstance(obj, list):
        print(f"{indent}[{len(obj)} item(s)]")
        for item in obj[:2]:
            _dump(item, indent + "  ", depth + 1)
    else:
        print(f"{indent}{str(obj)[:60]}")


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    address, city_state_zip = sys.argv[1], sys.argv[2]

    from api.services.sitex import SiteXConfig, SiteXClient

    config = SiteXConfig()
    if not config.validate():
        print("SITEX_CLIENT_ID / SITEX_CLIENT_SECRET are not set. Nothing sent.")
        sys.exit(2)
    print(f"base_url: {config.base_url}   feed: {config.feed_id}")
    print(f"looking up: {address}, {city_state_zip}\n")

    client = SiteXClient(config)
    try:
        await client.initialize()
        data = await client.search_by_address(address, city_state_zip)
    finally:
        await client.close()

    raw = data.raw_response or {}
    profile = (raw.get("Feed") or {}).get("PropertyProfile") or {}
    if not profile:
        print("No PropertyProfile in the response. Top-level keys:", list(raw))
        sys.exit(1)

    print("=" * 72)
    print("EVERY KEY UNDER Feed.PropertyProfile")
    print("=" * 72)
    for k in sorted(profile):
        v = profile[k]
        kind = type(v).__name__
        n = f" ({len(v)} keys)" if isinstance(v, dict) else (
            f" ({len(v)} items)" if isinstance(v, list) else "")
        print(f"  {k}  [{kind}{n}]")

    hits = [k for k in profile if any(h in k.lower() for h in SALE_HINTS)]
    print("\n" + "=" * 72)
    print(f"SECTIONS THAT LOOK LIKE SALE HISTORY: {hits or 'NONE'}")
    print("=" * 72)
    for k in hits:
        print(f"\n{k}:")
        _dump(profile[k])

    print("\n" + "=" * 72)
    if hits:
        print("VERDICT: SiteX returns the section(s) above and the parser reads")
        print("none of them. D-118's last-sale row is a PARSING ticket — add the")
        print("fields to PropertyData and _parse_response. Paste the block above;")
        print("the exact key names are what the mapping needs.")
    else:
        print("VERDICT: no sale-history section in this feed's PropertyProfile.")
        print("D-118's last-sale row cannot be built from SiteX on this feed, so")
        print("either the feed id needs to change (a commercial question) or the")
        print("row comes from the MLS with the coverage gap probe section 3b")
        print("describes — FSBO, off-market and inter-family transfers invisible.")
    print("\nOne lookup. Read only.")


if __name__ == "__main__":
    asyncio.run(main())
