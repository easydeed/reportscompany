#!/usr/bin/env python3
"""LR-011 operator replay. Read-only unless --apply and --reason are supplied.

Use only for a reviewed event list. Never retrieves events from Stripe.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'apps/api/src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event-id')
    parser.add_argument('--mode', choices=('live', 'test'), required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--reason')
    args = parser.parse_args()
    from api.config.billing import STRIPE_SECRET_KEY
    from api.db import db_conn
    from api.services.billing_envelope import expected_live_mode
    from api.services.billing_events import backlog, inspect_replay, process_receipt, list_receipts
    live = args.mode == 'live'
    if expected_live_mode(STRIPE_SECRET_KEY) is not live:
        parser.error('Configured server mode must match the selected receipt mode')
    if args.apply and (not args.event_id or not args.reason or not args.reason.strip()):
        parser.error('--apply requires --event-id and --reason')
    if not args.event_id:
        with db_conn() as (_, cur):
            result = {'backlog': backlog(cur), 'receipts': list_receipts(cur, live)}
    else:
        result = inspect_replay(args.event_id, live)
        if args.apply:
            if not result['replayable']:
                parser.error('Receipt is terminal or superseded; replay refused')
            result = process_receipt(args.event_id, live, replay_reason=args.reason)
    print(json.dumps(result, default=str))


if __name__ == '__main__':
    main()
