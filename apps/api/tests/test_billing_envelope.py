"""Offline fixtures only; the normalizer must never contact Stripe."""
from copy import deepcopy

import pytest

from api.services.billing_envelope import expected_live_mode, normalize_verified_event


def event():
    return {"id": "evt_fixture", "type": "customer.subscription.deleted",
            "livemode": True, "created": 1795000000,
            "api_version": "2025-10-29.clover", "data": {"object": {
                "id": "sub_fixture", "customer": "cus_fixture", "status": "canceled",
                "metadata": {"account_id": "11111111-1111-4111-8111-111111111111"},
                "items": {"data": [{"price": {"id": "price_fixture"},
                                    "current_period_end": 1796000000}]}}}}


def normalize(e):
    return normalize_verified_event(e, expected_live=True)


@pytest.mark.parametrize("prefix,expected", [
    ("sk_live_x", True), ("rk_live_x", True), ("sk_test_x", False),
    ("rk_test_x", False), ("bad", None), (None, None), ("sk_live_", None),
])
def test_mode_comes_only_from_configured_key_prefix(prefix, expected):
    assert expected_live_mode(prefix) is expected


def test_clover_item_period_and_legacy_top_level_period():
    e = event()
    assert normalize(e)["period_end"] == 1796000000
    obj = e["data"]["object"]
    obj["current_period_end"] = obj["items"]["data"][0].pop("current_period_end")
    e["api_version"] = "2024-06-20"
    assert normalize(e)["period_end"] == 1796000000


@pytest.mark.parametrize("bad", [None, True, "1796000000", -1, {}, []])
def test_unrecognised_cancellation_period_is_quarantined(bad):
    e = event()
    e["data"]["object"]["items"]["data"][0]["current_period_end"] = bad
    result = normalize(e)
    assert result["period_end"] is None
    assert result["reason"] == "period_shape_unsupported"


def test_conflicting_periods_are_never_guessed():
    e = event()
    e["data"]["object"]["current_period_end"] = 1794000000
    assert normalize(e)["reason"] == "period_shape_unsupported"


def test_missing_status_cannot_mutate_billing_state():
    e = event()
    del e['data']['object']['status']
    assert normalize(e)['reason'] == 'unsupported_subscription_status'


@pytest.mark.parametrize("bad", [None, [], "unexpected", {"object": []}])
def test_malformed_business_data_retains_receipt_identity(bad):
    e = event()
    e["data"] = bad
    result = normalize(e)
    assert result["event_id"] == "evt_fixture"
    assert result["reason"] == "invalid_subscription_reference"


@pytest.mark.parametrize("expected", [True, False])
def test_mode_mismatch_is_quarantined_in_both_directions(expected):
    e = event()
    e["livemode"] = not expected
    assert normalize_verified_event(e, expected_live=expected)["reason"] == "mode_mismatch"


def test_envelope_omits_payment_contact_data_and_arbitrary_metadata():
    e = event()
    obj = e["data"]["object"]
    obj.update(customer_email="sentinel@example.com", payment_method="secret_payment")
    obj["metadata"]["note"] = "secret_metadata"
    before = deepcopy(e)
    result = repr(normalize(e))
    for value in ("sentinel@example.com", "secret_payment", "secret_metadata"):
        assert value not in result
    assert e == before


def test_malformed_identity_is_rejected_without_inventing_receipt_id():
    e = event()
    e["created"] = True
    with pytest.raises(ValueError, match="invalid_event_identity"):
        normalize(e)
