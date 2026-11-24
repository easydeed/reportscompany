#!/usr/bin/env python3
"""LR-027: the observe-mode threshold report (design section 8, step 2).

READ ONLY. Counts and durations only: no account IDs, no incident member
identities, no addresses or numbers. Safe to paste into a PR or chat.

What it answers, for Jerry's threshold approval:

  Part A, what the monitor actually recorded with the proposed thresholds
  (`ops_alerts`, written in observe mode since 0069): per signal, incidents
  opened and resolved, how long they stayed open, how many members, how many
  re-opened within the flap window, and the email/SMS load the SAME incidents
  would have produced with sending switched on.

  Part B, headroom on the three count/share thresholds (report_failures,
  provider_refusals, send_not_attempted). It re-runs the monitor's own queries
  (worker/ops_signals.py, with `at=`) at every monitor interval across the
  window, so the numbers cannot drift from what the monitor checks: how often
  each would have tripped, the highest value seen, and the near misses.
  Those three read only terminal states (failed rows, refusals, finished
  runs), so replaying them at a past instant counts what the monitor saw then.

Usage (Jerry, against production, from a machine that already has access):

    DATABASE_URL=... python3 scripts/ops_threshold_report.py --hours 48

The URL is read from the environment and never printed. Every statement runs
in a READ ONLY transaction with a statement timeout; nothing is written.
"""
import argparse
import os
import statistics
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "worker" / "src"))

from worker import ops_monitor, ops_notify, ops_signals  # noqa: E402

RATE_SIGNALS = {
    "report_failures": (ops_signals.report_failures, "failed",
                        f">= {ops_signals.REPORT_FAILURES_MIN_COUNT.value:g} failed and "
                        f">= {ops_signals.REPORT_FAILURES_MIN_SHARE.value:.0%} of the hour's reports",
                        ops_signals.REPORT_FAILURES_MIN_COUNT.value),
    "provider_refusals": (ops_signals.provider_refusals, "refused",
                          f">= {ops_signals.PROVIDER_REFUSALS_MIN_COUNT.value:g} refusals and "
                          f">= {ops_signals.PROVIDER_REFUSALS_MIN_SHARE.value:.0%} of the hour's sends",
                          ops_signals.PROVIDER_REFUSALS_MIN_COUNT.value),
    "send_not_attempted": (ops_signals.send_not_attempted, "not_sent",
                           f">= {ops_signals.SEND_NOT_ATTEMPTED_MIN_COUNT.value:g} in an hour",
                           ops_signals.SEND_NOT_ATTEMPTED_MIN_COUNT.value),
}


def _minutes(delta) -> float:
    return delta.total_seconds() / 60 if delta is not None else 0.0


def _fmt_min(m: float) -> str:
    if m < 90:
        return f"{m:.0f} min"
    return f"{m / 60:.1f} h"


def incidents(cur, since, now) -> list[dict]:
    """Every incident open at any point in the window (counts and times only)."""
    cur.execute("""
        SELECT a.id, a.key, a.opened_at, a.resolved_at, a.member_count, a.members_truncated,
               (SELECT count(DISTINCT m.first_seen_at) FROM ops_alert_members m WHERE m.alert_id = a.id)
        FROM ops_alerts a
        WHERE a.opened_at <= %(now)s AND (a.resolved_at IS NULL OR a.resolved_at >= %(since)s)
        ORDER BY a.opened_at
    """, {"since": since, "now": now})
    rows = []
    for _id, key, opened, resolved, members, truncated, batches in cur.fetchall():
        rows.append({"key": key, "opened": opened, "resolved": resolved, "members": members,
                     "truncated": truncated, "batches": batches})
    return rows


def message_load(rows, now) -> dict:
    """What sending would have produced for these incidents (design section 5).

    Per incident: one `open` (email; SMS too for an SMS key unless it re-opened
    within the flap window), one `update` email per later run that added members,
    one `renotify` (email + SMS) per 6 h open, and one `resolved` (email + SMS).
    """
    flap = timedelta(minutes=ops_monitor.FLAP_WINDOW_MIN)
    by_key: dict = {}
    last_resolved: dict = {}
    texts_by_hour: dict = {}
    for r in sorted(rows, key=lambda r: r["opened"]):
        sms, _ = ops_notify._key_meta(r["key"])
        k = by_key.setdefault(r["key"], {"emails": 0, "texts": 0, "flapped_opens": 0})
        prev = last_resolved.get(r["key"])
        flapping = prev is not None and r["opened"] - prev <= flap
        k["flapped_opens"] += int(flapping)
        end = r["resolved"] or now
        renotifies = int((end - r["opened"]).total_seconds() // (ops_notify.RENOTIFY_HOURS * 3600))
        updates = max(r["batches"] - 1, 0)
        k["emails"] += 1 + updates + renotifies + (1 if r["resolved"] else 0)
        text_times = []
        if sms:
            if not flapping:
                text_times.append(r["opened"])
            text_times += [r["opened"] + timedelta(hours=ops_notify.RENOTIFY_HOURS * (n + 1))
                           for n in range(renotifies)]
            if r["resolved"]:
                text_times.append(r["resolved"])
        k["texts"] += len(text_times)
        for t in text_times:
            hour = t.replace(minute=0, second=0, microsecond=0)
            texts_by_hour[hour] = texts_by_hour.get(hour, 0) + 1
        if r["resolved"]:
            last_resolved[r["key"]] = r["resolved"]
    return {"by_key": by_key,
            "max_texts_in_an_hour": max(texts_by_hour.values(), default=0),
            "hours_over_cap": sum(1 for v in texts_by_hour.values() if v > ops_notify.SMS_CAP_PER_HOUR)}


def replay(cur, since, now, step: timedelta) -> dict:
    """Re-run each rate signal, as the monitor would have, at every step."""
    out = {}
    for key, (fn, field, _, count_threshold) in RATE_SIGNALS.items():
        values, trips, near, trip_hours = [], 0, 0, set()
        t = since + step
        while t <= now:
            reading = fn(cur, at=t)
            v = reading.value.get(field, 0)
            values.append(v)
            if reading.tripped:
                trips += 1
                trip_hours.add(t.replace(minute=0, second=0, microsecond=0))
            elif v >= count_threshold / 2:
                near += 1
            t += step
        out[key] = {"evaluations": len(values), "trips": trips, "trip_hours": len(trip_hours),
                    "near_misses": near, "max": max(values, default=0),
                    "p95": (statistics.quantiles(values, n=20)[-1] if len(values) >= 20 else max(values, default=0))}
    return out


def report(conn, hours: float, step_min: int) -> str:
    with conn.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '30s'")
        cur.execute("SELECT to_regclass('ops_alerts') IS NOT NULL")
        if not cur.fetchone()[0]:
            return "Migration 0069 (ops_alerts) is not applied here: nothing was observed."
        cur.execute("SELECT now()")
        now = cur.fetchone()[0]
        since = now - timedelta(hours=hours)
        cur.execute("SELECT min(opened_at) FROM ops_alerts")
        first = cur.fetchone()[0]
        rows = incidents(cur, since, now)
        load = message_load(rows, now)
        rates = replay(cur, since, now, timedelta(minutes=step_min))
        cur.execute("SELECT count(*) FROM ops_alert_notifications WHERE created_at >= %s", (since,))
        queued = cur.fetchone()[0]

    lines = [f"# LR-027 observe-mode threshold report",
             "",
             f"- Window: the last {hours:g} h, ending {now:%Y-%m-%d %H:%M %Z}.",
             f"- First incident ever recorded: {first:%Y-%m-%d %H:%M %Z}." if first else
             "- No incident has ever been recorded (an empty `ops_alerts` can also mean the monitor is not running).",
             f"- Notification rows created in the window: {queued} (0 expected while OPS_ALERTS_ENABLED is off).",
             "",
             "## A. Incidents the monitor recorded with the proposed thresholds",
             "",
             "| Signal | SMS | Opened | Still open | Re-opened within 30 min | Median open | Longest open | Most members | Emails if on | Texts if on |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    keys = [s.key for s in ops_signals.SIGNALS] + list(ops_monitor.HEARTBEAT_SIGNALS)
    for key in keys:
        mine = [r for r in rows if r["key"] == key]
        sms, _ = ops_notify._key_meta(key)
        if not mine:
            lines.append(f"| `{key}` | {'yes' if sms else 'email'} | 0 | 0 | 0 | – | – | – | 0 | 0 |")
            continue
        durations = [_minutes((r["resolved"] or now) - r["opened"]) for r in mine]
        k = load["by_key"][key]
        most = max(r["members"] for r in mine)
        lines.append(
            f"| `{key}` | {'yes' if sms else 'email'} | {len(mine)} | "
            f"{sum(1 for r in mine if r['resolved'] is None)} | {k['flapped_opens']} | "
            f"{_fmt_min(statistics.median(durations))} | {_fmt_min(max(durations))} | "
            f"{most}{'+' if any(r['truncated'] for r in mine) else ''} | {k['emails']} | {k['texts']} |")
    other = sorted({r["key"] for r in rows} - set(keys))
    for key in other:
        lines.append(f"| `{key}` | – | {sum(1 for r in rows if r['key'] == key)} | – | – | – | – | – | – | – |")
    lines += ["",
              f"- Most alert texts in any one clock hour: {load['max_texts_in_an_hour']} "
              f"(the cap is {ops_notify.SMS_CAP_PER_HOUR}; hours over it: {load['hours_over_cap']}).",
              "- Emails/texts are an estimate from the recorded incidents: open, member updates, a "
              f"renotify every {ops_notify.RENOTIFY_HOURS} h, and the recovery.",
              "",
              f"## B. Headroom on the count/share thresholds (replayed every {step_min} min)",
              "",
              "| Signal | Proposed threshold | Evaluations | Would have tripped | Hours tripped | Near misses (>= half the count) | Highest count | 95th percentile |",
              "|---|---|---|---|---|---|---|---|"]
    for key, (_, _, threshold, _) in RATE_SIGNALS.items():
        r = rates[key]
        lines.append(f"| `{key}` | {threshold} | {r['evaluations']} | {r['trips']} | {r['trip_hours']} | "
                     f"{r['near_misses']} | {r['max']:g} | {r['p95']:g} |")
    lines += ["",
              "Counts only. Read-only transaction; no identities, accounts or contact details."]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--hours", type=float, default=48.0)
    parser.add_argument("--step-minutes", type=int, default=5)
    args = parser.parse_args(argv)
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL (it is read, never printed).", file=sys.stderr)
        return 2
    import psycopg
    with psycopg.connect(url, connect_timeout=10) as conn:
        conn.read_only = True
        try:
            print(report(conn, args.hours, args.step_minutes))
        finally:
            conn.rollback()
    return 0


if __name__ == "__main__":
    sys.exit(main())
