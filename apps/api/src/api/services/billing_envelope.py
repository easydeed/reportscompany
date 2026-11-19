"""Allowlisted subscription facts from an already signature-verified event.

Pure normalization only: no Stripe requests, storage, or entitlement changes.
Unexpected business shapes retain a receipt identity and a quarantine reason.
"""
from collections.abc import Mapping
from uuid import UUID

SUBSCRIPTIONS = frozenset({
    "customer.subscription.created", "customer.subscription.updated",
    "customer.subscription.deleted",
})


def expected_live_mode(key: str | None) -> bool | None:
    for prefix, live in (("sk_live_", True), ("rk_live_", True),
                         ("sk_test_", False), ("rk_test_", False)):
        if key and key.startswith(prefix) and len(key) > len(prefix):
            return live
    return None


def _map(value):
    return value if isinstance(value, Mapping) else {}


def _text(value):
    return value if isinstance(value, str) and 0 < len(value) <= 255 else None


def _epoch(value):
    # bool is an int in Python, but never a valid Stripe timestamp.
    return value if type(value) is int and 0 < value <= 253402300799 else None


def normalize_verified_event(event: Mapping, *, expected_live: bool) -> dict:
    """Invalid identity raises; deterministic business errors are quarantined.

    The caller must verify the ORIGINAL bytes with Stripe before calling this.
    Never persist the original body or arbitrary metadata alongside this dict.
    """
    event_id, kind = _text(event.get("id")), _text(event.get("type"))
    live, created = event.get("livemode"), _epoch(event.get("created"))
    if not event_id or not kind or type(live) is not bool or created is None:
        raise ValueError("invalid_event_identity")
    out = {"event_id": event_id, "event_type": kind, "livemode": live,
           "created": created, "api_version": _text(event.get("api_version")),
           "subscription_id": None, "customer_id": None, "account_id": None,
           "status": None, "price_id": None, "period_end": None, "reason": None}
    if live != expected_live:
        out["reason"] = "mode_mismatch"
        return out
    if event.get("account") is not None:
        out["reason"] = "unsupported_account_context"
        return out
    if kind not in SUBSCRIPTIONS:
        return out
    obj = _map(_map(event.get("data")).get("object"))
    out.update(subscription_id=_text(obj.get("id")),
               customer_id=_text(obj.get("customer")), status=_text(obj.get("status")))
    candidate = _map(obj.get("metadata")).get("account_id")
    try:
        out["account_id"] = str(UUID(candidate)) if isinstance(candidate, str) else None
    except ValueError:
        pass
    if not out["subscription_id"] or not out["customer_id"] or not out["account_id"]:
        out["reason"] = "invalid_subscription_reference"
        return out
    items = _map(obj.get("items")).get("data")
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], Mapping):
        out["reason"] = "unsupported_subscription_items"
        return out
    item = items[0]
    out["price_id"] = _text(_map(item.get("price")).get("id"))
    if not out["price_id"]:
        out["reason"] = "missing_price"
        return out
    # Accept only explicit fixture-supported shapes. Conflicting periods must
    # never guess whether paid access has expired.
    legacy, modern = obj.get("current_period_end"), item.get("current_period_end")
    values = [v for v in (legacy, modern) if v is not None]
    if values and all(_epoch(v) is not None for v in values) and len(set(values)) == 1:
        out["period_end"] = values[0]
    elif kind == "customer.subscription.deleted":
        out["reason"] = "period_shape_unsupported"
    return out
