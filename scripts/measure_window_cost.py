#!/usr/bin/env python3
"""What does the six-month comp window actually cost? (D-132, D-145)

    python3 scripts/measure_window_cost.py tmp/market_snapshot_downey.json
    python3 scripts/measure_window_cost.py --raw tmp/downey_raw.json

WHY THIS EXISTS. Until D-145, `_closed_within_window` read `mls.closeDate`
while the feed writes `sales.closeDate`, so every closed listing looked
date-less, every one was kept, and the filter dropped nothing — ever. The
question "what does the window cost" therefore has no history to look at: the
answer was structurally zero, and the first real answer arrives with the
deploy.

This measures it two ways, and is explicit about which one it managed.

  SNAPSHOT MODE reads `tools/dump_market_snapshot.py`'s output. That file is
  aggregates plus five closed rows with their dates stripped, so it cannot
  run the filter. What it CAN give is the city's closing rate, which bounds
  the problem from above: a market closing N homes a month is not going to be
  emptied by a six-month window at CITY scale. It says nothing about any one
  subject's comp set after radius, sqft, beds and subtype have narrowed it,
  and this script will not pretend otherwise.

  RAW MODE reads `--raw-out`'s output and runs the REAL
  `_closed_within_window` — imported, not reimplemented — over every closed
  row at both windows. That is the measurement.

WHAT THE BOARD ALREADY SETTLES, before either mode runs. `minclosedate` is
sent on every closed ladder level, and D-074 confirmed in production that it
filters correctly: 60,874 closings in 90 days against 962,517 unfiltered. So
for `status=Closed` — the only closed path the wizard can reach — the vendor
was already applying the window server-side. What was void was the BACKSTOP,
not the window. The expected client-side drop on that path is near zero, and
a large number here would mean the vendor filter is not what D-074 measured.

The exception is `status=All`: no `minclosedate` is sent (it would drop the
active half), so the client pass is the only window on that path and this
week is the first time it has one.
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps/api/src"))

from api.routes.property import (  # noqa: E402
    COMP_CLOSE_WINDOW_DAYS,
    COMP_FALLBACK_WINDOW_DAYS,
    COMP_MIN_FOR_ANALYSIS,
    _closed_within_window,
)


def snapshot_mode(data: dict) -> int:
    counts = data.get("counts") or {}
    days = data.get("lookback_days")
    closed = counts.get("Closed")
    timelines = data.get("contract_timelines") or {}

    print(f"SNAPSHOT MODE — {data.get('city')}, lookback {days} days\n")
    if closed is None or not days:
        sys.exit("not a market snapshot: no `counts.Closed` / `lookback_days`")

    print(f"  closings in {days} days                {closed}")
    # `counts.Closed` is len(closed), and `closed` is filtered on
    # `close_date >= cutoff` — so every one of them carried sales.closeDate.
    print(f"  of those, carrying a close date       {closed} "
          f"(all of them: the count is filtered on it)")
    n_escrow = timelines.get("sample_size")
    if n_escrow is not None:
        print(f"  carrying BOTH close and contract date {n_escrow} "
              f"(escrow days computed for each)")

    rate = closed / days
    print(f"\n  implied rate                          {rate:.2f}/day")
    for window, label in ((COMP_CLOSE_WINDOW_DAYS, "six-month window"),
                          (COMP_FALLBACK_WINDOW_DAYS, "twelve-month (L6)")):
        print(f"  city-wide closings inside the {label:22s} ~{rate * window:.0f}")

    floor = COMP_MIN_FOR_ANALYSIS
    inside = rate * COMP_CLOSE_WINDOW_DAYS
    print(f"\n  COMP_MIN_FOR_ANALYSIS is {floor}. At city scale the six-month "
          f"window holds ~{inside:.0f}.")
    print("  THIS IS A CEILING, NOT THE ANSWER. The comps query narrows by "
          "radius, sqft\n  band, beds and subtype before any of these reach a "
          "report. A city with\n  ~%d closings can still yield fewer than %d "
          "comps for one address." % (inside, floor))
    print("\n  Snapshot mode cannot run the filter: `listings_sample` keeps five "
          "closed rows\n  and strips list_date, close_date and contract_date "
          "from each. Re-capture with\n  `--raw-out` and run this script with "
          "`--raw` for the real number.")
    return 0


def raw_mode(rows: list) -> int:
    if not isinstance(rows, list) or not rows:
        sys.exit("--raw wants a JSON list of raw listing rows "
                 "(tools/dump_market_snapshot.py --raw-out)")

    print(f"RAW MODE — {len(rows)} rows, running the real "
          f"`_closed_within_window`\n")

    status = Counter((r.get("mls") or {}).get("status") for r in rows)
    print("  by status: " + ", ".join(f"{k}={v}" for k, v in status.most_common()))

    closed = [r for r in rows if (r.get("mls") or {}).get("status") == "Closed"]
    if not closed:
        sys.exit("no Closed rows — nothing for a close-date window to act on")

    dated = [r for r in closed if (r.get("sales") or {}).get("closeDate")]
    print(f"  closed rows                           {len(closed)}")
    print(f"  carrying sales.closeDate              {len(dated)}")
    # A closed row with no close date is KEPT by the filter, on purpose. If
    # that is most of them, the window is weak for a reason the filter cannot
    # fix, and saying so matters more than the drop count.
    if len(dated) < len(closed):
        print(f"  ** {len(closed) - len(dated)} closed rows have NO close date. "
              f"Those are kept by design;\n     the window cannot act on them.**")

    print()
    for window in (COMP_CLOSE_WINDOW_DAYS, COMP_FALLBACK_WINDOW_DAYS):
        kept = _closed_within_window(closed, window)
        dropped = len(closed) - len(kept)
        pct = 100.0 * dropped / len(closed)
        print(f"  {window:>3}-day window: keeps {len(kept):>4} of {len(closed)}, "
              f"drops {dropped:>4}  ({pct:.1f}%)")

    six = len(_closed_within_window(closed, COMP_CLOSE_WINDOW_DAYS))
    twelve = len(_closed_within_window(closed, COMP_FALLBACK_WINDOW_DAYS))
    print(f"\n  L6 would readmit {twelve - six} sale(s) the six-month window hid.")
    if six < COMP_MIN_FOR_ANALYSIS:
        print(f"  ** city-wide, six months leaves {six} — below "
              f"COMP_MIN_FOR_ANALYSIS ({COMP_MIN_FOR_ANALYSIS}).\n"
              f"     Every report in this market reaches L6. **")
    else:
        print(f"  City-wide, six months leaves {six}, above "
              f"COMP_MIN_FOR_ANALYSIS ({COMP_MIN_FOR_ANALYSIS}).")
        print("  Still a ceiling: one address's comps are a subset after radius, "
              "sqft,\n  beds and subtype.")

    cutoff = (datetime.utcnow().date() - timedelta(days=COMP_CLOSE_WINDOW_DAYS))
    stale = [r for r in dated
             if str((r.get("sales") or {})["closeDate"])[:10] < cutoff.isoformat()]
    if stale:
        print(f"\n  Oldest few sales the six-month window drops:")
        for r in sorted(stale, key=lambda r: r["sales"]["closeDate"])[:5]:
            print(f"    {r['sales']['closeDate'][:10]}  "
                  f"{(r.get('address') or {}).get('full', '?')}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture", type=Path, nargs="?",
                    default=REPO / "tmp/market_snapshot_downey.json",
                    help="a market snapshot (aggregates). Default: the Downey one.")
    ap.add_argument("--raw", type=Path, default=None,
                    help="a raw-row capture from `dump_market_snapshot.py "
                         "--raw-out`. This is the mode that runs the filter.")
    args = ap.parse_args()

    if args.raw:
        return raw_mode(json.loads(args.raw.read_text(encoding="utf-8")))
    return snapshot_mode(json.loads(args.capture.read_text(encoding="utf-8")))


if __name__ == "__main__":
    sys.exit(main())
