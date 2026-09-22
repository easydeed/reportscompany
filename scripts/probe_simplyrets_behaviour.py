#!/usr/bin/env python3
"""
Ask the SimplyRETS feed three questions this repository has been guessing at.

READ ONLY. A dozen or so GET requests to /properties — the script counts them
and prints the exact number at the end, because a hand-maintained count in a
docstring is wrong the first time somebody adds a check and does not update it.
It was already wrong once. No writes, no state, nothing cached. Safe to run
against production at any time.

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
from datetime import datetime, timedelta
import urllib.error
import urllib.request
from collections import Counter

BASE = os.getenv("SIMPLYRETS_BASE_URL", "https://api.simplyrets.com")

def _most_common_zip(active_result):
    """
    The ZIP with the most listings in the active sample, and how many.

    Derived from the feed rather than hardcoded, so the filtered-count check
    always has a non-empty subset to narrow to — see the comment at its call
    site for what a hardcoded one got wrong.
    """
    if not active_result:
        return None, 0
    counts = Counter(
        (row.get("address") or {}).get("postalCode")
        for row in active_result[0]
        if (row.get("address") or {}).get("postalCode")
    )
    if not counts:
        return None, 0
    return counts.most_common(1)[0]
DEMO_USER = "simplyrets"
TIMEOUT = 30


# Counted rather than documented. See the module docstring.
REQUESTS = {"sent": 0, "failed": 0}


def _get(auth, query, label):
    """One GET. Returns (rows, status_counts, seconds, headers) or None."""
    REQUESTS["sent"] += 1
    url = f"{BASE}/properties?{query}"
    req = urllib.request.Request(
        url, headers={"Authorization": auth, "Accept": "application/json"}
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read())
            headers = dict(resp.headers)
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:120].decode("utf-8", "replace")
        print(f"  {label:44s} HTTP {exc.code}  {detail}")
        REQUESTS["failed"] += 1
        return None
    except Exception as exc:  # noqa: BLE001 — a probe reports, it does not raise
        print(f"  {label:44s} {type(exc).__name__}: {exc}")
        REQUESTS["failed"] += 1
        return None
    elapsed = time.time() - started
    counts = Counter((row.get("mls") or {}).get("status") for row in body)
    total = headers.get("X-Total-Count")
    print(f"  {label:44s} {len(body):5d} rows  {elapsed:5.2f}s  {dict(counts)}"
          + (f"  X-Total-Count={total}" if total else ""))
    return body, counts, elapsed, headers


# Parameters that are NOT filters — they change the shape of the answer, not
# which rows are in it — so a canary says nothing about them. Listed explicitly
# rather than omitted, so the next person can see the survey considered them.
NON_FILTERING = ("limit", "offset", "sort", "count", "vendor")


def _canary_name(param):
    """
    A deliberately wrong spelling of a real parameter.

    Lowercasing is the realistic typo for the camelCase ones and is exactly the
    mistake this section was written after making. For names that are already
    lowercase, a transposition — still a name the API has never heard of, which
    is the only property that matters.
    """
    lowered = param.lower()
    if lowered != param:
        return lowered
    return param[:-2] + param[-1] + param[-2] if len(param) > 2 else param + "x"


def _param_canaries(auth, active, verdicts):
    """
    One correct/incorrect pair per filtering parameter, compared on
    X-Total-Count against an unfiltered baseline.
    """
    if not active or not active[0]:
        print("  (no active sample — cannot derive values that must bite)")
        return

    rows = active[0]

    def _field(path, default=None):
        """First non-null value of a dotted path across the sample."""
        for row in rows:
            cur = row
            for part in path.split("."):
                cur = (cur or {}).get(part) if isinstance(cur, dict) else None
            if cur not in (None, ""):
                return cur
        return default

    prices = sorted(r["listPrice"] for r in rows if r.get("listPrice"))
    median = prices[len(prices) // 2] if prices else None
    beds = sorted(b for b in ((r.get("property") or {}).get("bedrooms") for r in rows) if b)
    baths = sorted(b for b in ((r.get("property") or {}).get("bathsFull") for r in rows) if b)

    # (parameter, value, why this value must narrow)
    candidates = [
        ("postalCodes", _field("address.postalCode"), "one ZIP out of several"),
        ("type", _field("property.type"), "one property type"),
        ("subtype", _field("property.subType") or _field("property.subTypeText"),
         "one property subtype"),
        ("minprice", median, "at least the median list price"),
        ("maxprice", median, "at most the median list price"),
        ("minbeds", beds[len(beds) // 2] if beds else None, "at least the median bedrooms"),
        ("minbaths", baths[len(baths) // 2] if baths else None, "at least the median bathrooms"),
        ("cities", _field("address.city"), "one city — `cities` is the production location param"),
        ("q", _field("address.city"), "fuzzy search on one city — the demo/fallback location param"),
        ("minclosedate", (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
         "the last 90 days — on Active this should narrow to nothing or be inert; "
         "its real test is section 2b"),
        ("mindate", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
         "the last 30 days — D-075 says this one is ignored"),
        ("maxdate", (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d"),
         "ten years ago — should exclude almost everything"),
    ]

    baseline = _get(auth, "status=Active&limit=1&count=true", "  baseline: status=Active")
    try:
        unfiltered = int(baseline[3].get("X-Total-Count"))
    except (TypeError, ValueError, IndexError):
        print("  (no X-Total-Count on the baseline — cannot compare)")
        return

    ignored, working, untestable = [], [], []

    for param, value, why in candidates:
        if value in (None, ""):
            untestable.append(f"{param} (no value in the sample to narrow with)")
            continue
        wrong = _canary_name(param)
        right_r = _get(auth, f"status=Active&{param}={value}&limit=1&count=true",
                       f"  {param}={value}")
        wrong_r = _get(auth, f"status=Active&{wrong}={value}&limit=1&count=true",
                       f"  canary {wrong}={value}")

        def _t(r):
            try:
                return int(r[3].get("X-Total-Count"))
            except (TypeError, ValueError, IndexError):
                return None

        right, wrong_total = _t(right_r), _t(wrong_r)
        if right is None:
            untestable.append(f"{param} (no count header on the filtered query)")
        elif right >= unfiltered:
            ignored.append(f"{param}={value} returned {right} of {unfiltered} ({why})")
        elif wrong_total is not None and wrong_total < unfiltered:
            # The misspelling ALSO narrowed, so this feed is not spelling-strict
            # and the canary proves nothing either way.
            working.append(f"{param} filters ({right} of {unfiltered}), but the "
                           f"canary `{wrong}` narrowed too — this feed is not "
                           f"spelling-strict, so a typo here would NOT widen")
        else:
            working.append(f"{param} filters ({right} of {unfiltered}); "
                           f"`{wrong}` returned {wrong_total} — ignored, as expected")

    verdicts["D-085"] = (
        ("SILENTLY IGNORED: " + "; ".join(ignored) + ". "
         if ignored else "No parameter was silently ignored. ")
        + f"Working: {len(working)}. "
        + (f"Not testable on this feed: {', '.join(untestable)}. " if untestable else "")
        + "A parameter listed as ignored is accepted with no error and widens "
          "the query to the whole feed — on a count that reads as a big market, "
          "not as a bug. Parameters that change shape rather than membership "
          f"({', '.join(NON_FILTERING)}) are not canaried."
    )
    for line in working:
        print(f"      ok: {line}")
    for line in ignored:
        print(f"      IGNORED: {line}")
    for line in untestable:
        print(f"      untestable: {line}")


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
    print("Read only throughout; the request count is printed at the end.\n")

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

    # ── 2b. minclosedate, a date INSIDE the range (D-074) ───────────────────
    #
    # ADDED after the first production run came back AMBIGUOUS: a future
    # minclosedate returned 1 of 500 rows — not 0, not 500. A single check
    # against a far-future date cannot tell "filters, with a null-handling
    # leak" from "ignored". The ambiguity was a gap in this probe, not only in
    # the answer, so the probe now asks a second question whose answer
    # separates them.
    print("2b. …and does it filter at a date inside the real range?")
    ninety = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    closed_90 = _get(auth, f"status=Closed&minclosedate={ninety}&limit=500",
                     f"  + minclosedate={ninety} (90d)")

    # COMPARE TOTALS, NOT PAGE COUNTS. THIS IS THE FIX FOR THIS SECTION'S OWN
    # VERDICT.
    #
    # The first production run of this section reported:
    #
    #     status=Closed (baseline)              500 rows
    #     + minclosedate=<90d>                  500 rows
    #     "CONFIRMED — a 90-day window returned 500 of 500 (a real subset)"
    #
    # 500 of 500 is not a subset. Both numbers are THIS SCRIPT'S `limit=500`,
    # and two capped counts are indistinguishable from the parameter being
    # ignored. The script's own closing paragraph says to read 500 as "at least
    # 500 exist, not a cap" — and then its D-074 logic read it as a meaningful
    # comparison, two sections up. Fifth instance of the named trap, in the file
    # that warns about it.
    #
    # `count=true` is now confirmed in production (section 4, X-Total-Count on a
    # `limit=1` request), so the real totals are one cheap request each and the
    # comparison can be exact.
    count_all = _get(auth, "status=Closed&limit=1&count=true",
                     "  count: status=Closed")
    count_90 = _get(auth, f"status=Closed&minclosedate={ninety}&limit=1&count=true",
                    f"  count: + minclosedate={ninety}")

    def _total(result):
        if not result:
            return None
        raw = result[3].get("X-Total-Count")
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    total_all, total_90 = _total(count_all), _total(count_90)

    if closed_all and closed_90 and closed_future:
        n_all, n_90, n_future = len(closed_all[0]), len(closed_90[0]), len(closed_future[0])

        # THE DECIDING COMPARISON IS `future < all`, not `future == 0`.
        # The first version of this asked whether a future date returned
        # nothing, which cannot distinguish "ignored" from "filters, with a few
        # null closeDates leaking through" — and production returned 1 of 500,
        # landing in exactly that gap. A parameter that returns FEWER rows than
        # no parameter at all is filtering; everything after that is about how
        # well.
        filters_at_all = n_future < n_all

        # Any row that survives a far-future cutoff is evidence about HOW it
        # leaks. Printed rather than described, so nobody has to go and fetch
        # it by hand.
        if n_future:
            print(f"  {n_future} row(s) survived a 2030 cutoff — their closeDate:")
            for row in closed_future[0][:5]:
                mls = row.get("mls") or {}
                print(f"      mlsId={row.get('mlsId')}  "
                      f"closeDate={mls.get('closeDate', row.get('closeDate', '<absent>'))!r}  "
                      f"listDate={row.get('listDate', '<absent>')!r}")

        if not filters_at_all:
            verdicts["D-074"] = (
                f"NOT CONFIRMED — a future minclosedate returned all {n_all} "
                f"rows, so the parameter is accepted and ignored. The 210-day "
                f"workaround is the right design, and what remains is whether "
                f"210 days is the right window."
            )
        elif total_all is None or total_90 is None:
            verdicts["D-074"] = (
                f"HALF CONFIRMED — it filters (a future cutoff returned "
                f"{n_future} where no cutoff returned {n_all}), but this feed "
                f"did not return X-Total-Count, so the 90-day window cannot be "
                f"corroborated: both page counts are capped at this script's "
                f"limit and prove nothing. Removing the 210-day workaround is "
                f"still safe under the defensive posture (minclosedate sent AND "
                f"close_date filtered client-side). Do NOT drop the client-side "
                f"filter or switch the denominator to a count until this is "
                f"settled."
            )
        elif total_90 == 0:
            # BEFORE the `total_90 < total_all` branch, not after. 0 < 13 is
            # true, so on a feed with no recent closed sales the subset branch
            # claimed "a genuine subset" from an empty result — which is the
            # same mistake this section was rewritten to fix, one branch over.
            # Caught by running it against the demo feed, which has none.
            verdicts["D-074"] = (
                f"CONFIRMED that it filters (future={n_future} < all={n_all}), "
                f"but X-Total-Count says this feed has NO closed sales in the "
                f"last 90 days ({total_all} closed in total), so the window "
                f"cannot be corroborated from it — an empty result is not a "
                f"subset. The workaround is still removable; confirm on a feed "
                f"with recent sales before relying on the numerator."
            )
        elif total_90 < total_all:
            verdicts["D-074"] = (
                f"CONFIRMED — minclosedate filters, at a real date. "
                f"X-Total-Count for the 90-day window is {total_90} against "
                f"{total_all} with no cutoff — a genuine subset, measured on "
                f"the feed's own totals rather than on page counts that are "
                f"both capped at this script's limit. A future cutoff returned "
                f"{n_future}"
                + (" — see the closeDate values printed above; a null or "
                   "malformed date leaking through is not a failure to filter."
                   if n_future else ".")
                + " market_trends.py's 210-day listDate workaround is "
                  "unnecessary AND lossy: it drops long-DOM recent sales, "
                  "deflating the sales rate and inflating months of supply. "
                  "Remove minlistdate and filter on close date."
            )
        elif total_90 == total_all and total_all > 0:
            verdicts["D-074"] = (
                f"AMBIGUOUS at an in-range date — X-Total-Count is {total_90} "
                f"both with and without a 90-day cutoff. Either every closed "
                f"sale in this feed is from the last 90 days (check the "
                f"baseline: {total_all}), or the parameter is only honoured for "
                f"some dates. The future-cutoff result ({n_future} of {n_all}) "
                f"still shows it filters somewhere. Do not switch the "
                f"denominator to a count on this evidence."
            )
        else:
            verdicts["D-074"] = (
                f"UNEXPECTED — the 90-day window returned MORE than no window "
                f"at all ({total_90} against {total_all}). That should not be "
                f"possible; paste the output rather than acting on it."
            )
    print()

    # ── 4. the exact total, without paging (D-081) ──────────────────────────
    print("4. Does count=true return X-Total-Count? (D-081 — the months-of-supply numerator)")
    _get(auth, "status=Active&limit=1", "  status=Active&limit=1           ")
    unfiltered = _get(auth, "status=Active&limit=1&count=true",
                      "  status=Active&limit=1&count=true")

    # AND DOES THE HEADER SURVIVE A FILTER?
    #
    # The first production run confirmed the header on an UNFILTERED query —
    # 70,760, the whole feed. `count_properties` never asks that question: the
    # numerator is per area, so every real call carries a `postalCodes` filter
    # alongside `count=true` (query_builders.py:76). A header present on the
    # bare query and unfiltered on a narrowed one would make every
    # months-of-supply figure the size of the entire MLS.
    #
    # THE ZIP IS TAKEN FROM THE FEED, NOT HARDCODED. An earlier draft of this
    # check used a fixed ZIP from the service area; on a feed that has no
    # listings there, "filtered total == unfiltered total" is indistinguishable
    # from the filter being ignored, and the check reports BROKEN for a feed
    # that is fine. Using the most common ZIP in the sample above guarantees a
    # non-empty subset on whatever feed this is pointed at, and costs no extra
    # request.
    probe_zip, probe_zip_n = _most_common_zip(active)

    # AND A CANARY, BECAUSE THIS CHECK'S FIRST RUN FAILED FOR THE WRONG REASON.
    #
    # It asked for `postalcodes=` — lowercase — and got the whole feed back,
    # which it duly reported as "the header IGNORES the filter: BROKEN". The
    # feed was fine. SimplyRETS parameter names are CASE-SENSITIVE, measured
    # against the demo feed:
    #
    #     postalCodes=77018  ->  X-Total-Count=5
    #     postalcodes=77018  ->  X-Total-Count=42   (the whole feed)
    #     postalcode=77018   ->  X-Total-Count=42
    #     (no filter)        ->  X-Total-Count=42
    #
    # An unrecognised parameter is accepted and ignored — the same silent
    # widening as D-075's `mindate`, and far more dangerous here, because an
    # ignored filter on a COUNT does not look wrong. It looks like a big market.
    #
    # So the misspelling is sent deliberately. If it comes back filtered, this
    # feed is not case-sensitive and the canary is meaningless; if it comes back
    # unfiltered, a "filter ignored" verdict on the real spelling means the feed
    # and not the spelling.
    filtered = _get(auth, f"status=Active&postalCodes={probe_zip}&limit=1&count=true",
                    f"  status=Active&postalCodes={probe_zip}&count=true")
    canary = _get(auth, f"status=Active&postalcodes={probe_zip}&limit=1&count=true",
                  f"  canary: postalcodes (lowercase, wrong)")

    def _header_total(result):
        if not result:
            return None
        try:
            return int(result[3].get("X-Total-Count"))
        except (TypeError, ValueError):
            return None

    total_unfiltered = _header_total(unfiltered)
    total_filtered = _header_total(filtered)
    total_canary = _header_total(canary)
    canary_was_ignored = (
        total_canary is not None
        and total_unfiltered is not None
        and total_canary >= total_unfiltered
    )

    if probe_zip is None:
        verdicts["D-081"] = (
            "INCONCLUSIVE — no postalCode appeared in the active sample, so "
            "there was nothing to narrow the count with. The header's behaviour "
            "under a filter is the part that matters for the numerator."
        )
    elif total_unfiltered is None:
        verdicts["D-081"] = (
            "NOT CONFIRMED — count=true returned no X-Total-Count header on "
            "this feed. The numerator has to be paged; D-078's copy fix is then "
            "the whole answer and the limit needs raising."
        )
    elif total_filtered is None:
        verdicts["D-081"] = (
            f"HALF CONFIRMED — the header is present unfiltered "
            f"({total_unfiltered}) and ABSENT when a postalCodes filter is "
            f"added. `count_properties` always filters, so it would get None "
            f"and months of supply would refuse to publish — safe, but the "
            f"feature does not work. Page the numerator instead."
        )
    elif total_filtered >= total_unfiltered:
        verdicts["D-081"] = (
            f"BROKEN — the header IGNORES the filter: {total_filtered} for "
            f"postalCodes={probe_zip} against {total_unfiltered} feed-wide, "
            f"when the sample above shows {probe_zip_n} listing(s) in that ZIP. "
            f"Every months-of-supply numerator would be the size of the entire "
            f"MLS. Do not ship count_properties against this feed."
        )
    else:
        verdicts["D-081"] = (
            f"CONFIRMED — count=true returns X-Total-Count, and it respects "
            f"filters: {total_unfiltered} active feed-wide, {total_filtered} "
            f"for postalCodes={probe_zip}. The months-of-supply numerator can "
            f"be one cheap request instead of paging, which removes D-078's "
            f"ceiling rather than raising it."
            + (f" Parameter names are case-sensitive on this feed: the "
               f"lowercase `postalcodes` canary returned {total_canary}, the "
               f"whole feed, silently — the same accepted-and-ignored shape as "
               f"D-075."
               if canary_was_ignored else "")
        )
    print()

    # ── 5. every filtering parameter, with a canary (D-085) ─────────────────
    #
    # D-075 GENERALISED FROM ONE PARAMETER TO ALL OF THEM.
    #
    # `mindate` is accepted and ignored. So is `postalcodes` — the lowercase
    # spelling of a parameter that works — which is how this section came to
    # exist: the D-081 check above reported "the header IGNORES the filter" and
    # the feed was fine. Measured:
    #
    #     postalCodes=77018  ->  5        postalcodes=77018  ->  42 (everything)
    #
    # SimplyRETS accepts an unrecognised parameter and ignores it, with no
    # error. A misspelling anywhere in this client silently WIDENS the query,
    # and on a count that does not look wrong — it looks like a big market.
    #
    # So: every filtering parameter the client sends, each with a deliberately
    # misspelled twin. Correct returning FEWER than unfiltered proves the filter
    # bites. Wrong returning the SAME as unfiltered proves names are
    # case/spelling sensitive and the canary is meaningful.
    #
    # EVERY VALUE IS TAKEN FROM THE FEED, for the reason the hardcoded ZIP
    # taught: a filter whose value matches nothing narrows to zero, and a
    # filter whose value matches everything narrows to nothing, and neither
    # distinguishes "works" from "ignored". Values are picked from the sample in
    # section 1 so each one MUST bite.
    print("5. Does every filtering parameter actually filter? (canary pairs)")
    _param_canaries(auth, active, verdicts)
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
    for defect in ("D-074", "D-075", "D-076", "D-081", "D-085"):
        print(f"\n{defect}: {verdicts.get(defect, 'INCONCLUSIVE — a request failed above')}")
    print("\n" + "=" * 72)
    print(f"{REQUESTS['sent']} GET request(s) sent"
          + (f", {REQUESTS['failed']} failed" if REQUESTS["failed"] else ", none failed")
          + ". Read only throughout.")
    print("Paste this whole output back. The wording of each verdict is what "
          "goes on the defect entry.")
    if active:
        print(f"\nIncidentally: {len(active[0])} active listings came back in "
              f"{active[2]:.2f}s on a single request with limit=500. That 500 is "
              f"THIS SCRIPT'S limit, not an API ceiling — fetch_properties pages "
              f"at 500 up to 1000. Read it as 'at least 500 exist', not as a cap "
              f"(see D-078, D-081).")


if __name__ == "__main__":
    main()
