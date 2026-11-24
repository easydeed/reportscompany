# LR-027: observe-mode threshold report

Design: `LR-027_OPERATIONAL_ALERTS.md`, section 8, step 2: "Observe for 48 h, compare
the proposed thresholds with real traffic, and adjust; **[JERRY] approves the values.**"

This page is how that comparison is made. The numbers come from production, which only
Jerry can read, so the results section stays empty until he runs the report.

## Run it (Jerry)

From a machine that already has production database access:

```
DATABASE_URL=<production, read-only role if you have one> \
  python3 scripts/ops_threshold_report.py --hours 48
```

- **Read only.** The connection is opened `read_only`, every statement has a 30 s timeout, and
  the transaction is rolled back. It writes nothing.
- **Counts only.** No account IDs, incident members, addresses or phone numbers are printed. The
  output is safe to paste into the PR or to Claude Code. The URL is read from the environment
  and never printed. **Do not paste the URL.**
- **Cost:** 48 h at the monitor's 5-minute cadence is 576 replay instants, about 4,000 small
  queries, each over a one-hour window. It took about a second on the local database; expect a
  minute or two on production. `--step-minutes 15` cuts that by two thirds.

## What it reports

**A. What the monitor actually recorded**, from `ops_alerts`, which observe mode has written
since migration 0069. For each signal it lists:
- incidents opened, still open, and re-opened within 30 minutes (flapping);
- median and longest time open;
- the most members;
- the **emails and texts the same incidents would have sent** with alerts switched on: the
  open, member updates, a renotify every 6 h, and the recovery, with the flap rule applied;
- the most alert texts in any one hour, against the 10-per-hour cap.

**B. Headroom on the three count/share thresholds.** For `report_failures`,
`provider_refusals` and `send_not_attempted`, the report re-runs the monitor's **own queries**
(`worker/ops_signals.py`, with a past `at=`) every 5 minutes across the window.
- It cannot drift from what the monitor checks: it is the same code.
- These three count only terminal states (failed rows, refusals, finished runs), so a replay at
  a past instant sees what the monitor saw then.
- For each one it reports how often it would have tripped, the near misses (at least half the
  count threshold), the highest count, and the 95th percentile.

## How to read it (proposed decision rules)

| Finding | Suggested decision |
|---|---|
| A signal never opened, and section B shows no near misses | Keep the proposed value. |
| An "any" signal (`schedule_overdue`, `report_stuck`, `dispatch_stranded`, `send_needs_review`, `consumer_delivery_stuck`) opened, and each incident was a real problem | Keep it. That is the alert working. |
| An "any" signal opened for something that was not a problem | Fix the signal's definition (a code change and review), not the number. |
| A signal re-opened within 30 minutes more than once | It flaps. Discuss a longer window before switching texts on. |
| Section B shows frequent near misses on a count threshold | Keep the count. Note that the margin is thin, and look again after the first week. |
| The estimated texts are more than a few a day, or any hour is near the cap of 10 | Too noisy to text. Consider making that signal email-only. |

The thresholds stay proposals until Jerry records his approval in `DECISIONS_AND_LANES.md`.
Then come the destinations, the test alert, the pinger, and `OPS_ALERTS_ENABLED=1`.

## Results

_Pending Jerry's run. Paste the report's output here, or into the PR, and Claude Code writes up
the recommendation against the rules above._
