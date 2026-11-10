#!/usr/bin/env python3
"""
Held and stale consumer deliveries and agent notifications: list them, hold
them, and record what an operator found (LR-020 §6).

    DATABASE_URL=... python scripts/ops/held_sends.py list [--stage consumer|agent]
                     [--state held|stale|all] [--older-than MINUTES]
    DATABASE_URL=... python scripts/ops/held_sends.py hold REPORT --stage S --attempt A --operator NAME
    DATABASE_URL=... python scripts/ops/held_sends.py resolve REPORT --stage S --attempt A --sent
                     --provider-id SID_OR_EMAIL_ID [--sent-at ISO8601] --evidence TEXT --operator NAME
    DATABASE_URL=... python scripts/ops/held_sends.py resolve REPORT --stage S --attempt A --not-sent
                     --evidence TEXT --operator NAME

THIS TOOL NEVER SENDS. It calls no provider and enqueues nothing. It writes the
database only, and every write is conditional on the exact stage, attempt and
state you name.

When to use which:
  --sent       You found the provider's record of THIS attempt: the Twilio
               message (search the attempt's number from a minute before its
               claim time to ten minutes after) or the Resend email (the
               attempt's Idempotency-Key, shown by `list`). Give its SID or
               email id. A consumer text debits one SMS credit, once.
  --not-sent   You have POSITIVE evidence the provider did not accept it: a
               provider record of rejection, or a provider-side search covering
               the whole window that shows nothing. Not finding it in a quick
               dashboard search is not enough. The stage becomes `failed`; a new
               send is a separate decision (re-enqueue the report), and it will
               claim a new attempt.
  neither      If you cannot tell, leave it held.

Agent-stage resolutions never change the homeowner's report or credits.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "worker" / "src"))

from worker import consumer_delivery as cd  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list", help="held and stale attempts")
    ls.add_argument("--stage", choices=cd.STAGES)
    ls.add_argument("--state", choices=("held", "stale", "all"), default="all")
    ls.add_argument("--older-than", type=int, default=0, metavar="MINUTES")
    ls.add_argument("--json", action="store_true")

    hold = sub.add_parser("hold", help="move a stale 'sending' attempt to needs_review")
    hold.add_argument("report_id")
    hold.add_argument("--stage", choices=cd.STAGES, required=True)
    hold.add_argument("--attempt", required=True)
    hold.add_argument("--operator", required=True)

    res = sub.add_parser("resolve", help="record what the provider's own records show")
    res.add_argument("report_id")
    res.add_argument("--stage", choices=cd.STAGES, required=True)
    res.add_argument("--attempt", required=True)
    which = res.add_mutually_exclusive_group(required=True)
    which.add_argument("--sent", action="store_true")
    which.add_argument("--not-sent", action="store_true")
    res.add_argument("--provider-id")
    res.add_argument("--sent-at")
    res.add_argument("--evidence", required=True)
    res.add_argument("--operator", required=True)

    args = parser.parse_args(argv)
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    import psycopg
    with psycopg.connect(url, autocommit=True) as conn:
        if args.cmd == "list":
            rows = cd.list_held(conn.cursor(), stage=args.stage, state=args.state,
                                older_than_minutes=args.older_than)
            if args.json:
                print(json.dumps(rows, indent=2))
            else:
                for r in rows:
                    print(f"{r['report_id']}  {r['stage']:<8} {r['channel']:<5} {r['state']:<12} "
                          f"attempt={r['attempt_id']}  age={r['age_minutes']}m  to={r['destination']}  "
                          f"provider_id={r['provider_id'] or '-'}  replayed={r['replayed']}"
                          + (f"  key={r['idempotency_key']}" if r['idempotency_key'] else "")
                          + f"\n    {r['outcome'] or ''}")
                print(f"{len(rows)} attempt(s)")
            return 0
        try:
            if args.cmd == "hold":
                cd.hold_stale(conn, args.report_id, stage=args.stage, attempt_id=args.attempt,
                              operator=args.operator)
            elif args.sent:
                cd.resolve_sent(conn, args.report_id, stage=args.stage, attempt_id=args.attempt,
                                provider_id=args.provider_id, sent_at=args.sent_at,
                                evidence=args.evidence, operator=args.operator)
            else:
                cd.resolve_not_sent(conn, args.report_id, stage=args.stage, attempt_id=args.attempt,
                                    evidence=args.evidence, operator=args.operator)
        except cd.ResolutionRefused as e:
            print(f"refused, nothing changed: {e}", file=sys.stderr)
            return 1
        print("done")
        return 0


if __name__ == "__main__":
    sys.exit(main())
