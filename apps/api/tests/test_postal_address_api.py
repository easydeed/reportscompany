"""GET/PUT /v1/account/postal-address: an account's own address for its mail (D-079).

Jerry, 2026-10-30: per account, on `affiliate_branding.postal_address`.
Regular accounts have no branding row, so the first save makes one. An empty
save clears the field and never errors. With none set, the emails carry the
platform address, and the GET says which address is in use and whose it is.
"""
import os

import pytest

from test_rep_seats import _auth, client, world  # noqa: F401 — pytest fixtures, used by name
from test_company_admin_role import member  # noqa: F401

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")
PLATFORM = "440 Rte. 66, Glendora, CA 91740"
PATH = "/v1/account/postal-address"


def _get(client, email):
    r = client.get(PATH, headers=_auth(client, email))
    assert r.status_code == 200, r.text
    return r.json()


def _put(client, email, value, **extra):
    return client.put(PATH, json={"postal_address": value, **extra}, headers=_auth(client, email))


def _row(account_id):
    with psycopg.connect(DB_URL) as conn:
        return conn.execute(
            "SELECT brand_display_name, postal_address FROM affiliate_branding WHERE account_id = %s",
            (account_id,)).fetchone()


def test_a_regular_account_with_no_branding_row_can_set_one(client, world):
    me = world.email("ag-a1a")
    assert _row(world.a1a) is None, "the premise: a regular account has no branding row"
    before = _get(client, me)
    assert before == {"postal_address": None, "can_edit": True, "source": "platform",
                      "in_use": PLATFORM, "company_name": None, "platform_address": PLATFORM}

    r = _put(client, me, "  12 Oak Ave,\n  Anytown, CA 90000 ")
    assert r.status_code == 200, r.text
    assert r.json()["postal_address"] == "12 Oak Ave, Anytown, CA 90000"
    assert r.json()["source"] == "own" and r.json()["in_use"] == "12 Oak Ave, Anytown, CA 90000"
    assert _row(world.a1a) == ("Seat Agent ag-a1a", "12 Oak Ave, Anytown, CA 90000")
    assert _get(client, me)["source"] == "own"


@pytest.mark.parametrize("empty", ["", "   ", "\n\t", None])
def test_an_empty_save_clears_it_and_never_errors(client, world, empty):
    me = world.email("ag-a1a")
    assert _put(client, me, "12 Oak Ave, Anytown, CA 90000").status_code == 200
    r = _put(client, me, empty)
    assert r.status_code == 200, r.text
    assert r.json()["postal_address"] is None
    assert r.json()["source"] == "platform" and r.json()["in_use"] == PLATFORM
    assert _row(world.a1a)[1] is None


def test_an_empty_save_on_an_account_with_no_row_is_fine_too(client, world):
    r = _put(client, world.email("ag-a1b"), "")
    assert r.status_code == 200, r.text
    assert r.json()["source"] == "platform"


def test_only_an_over_long_address_or_an_unknown_field_is_refused(client, world):
    me = world.email("ag-a1a")
    assert _put(client, me, "x" * 301).status_code == 422
    assert _put(client, me, "1 A St", office="nope").status_code == 422
    assert _row(world.a1a) is None, "a refused save wrote something"


def test_the_company_admin_sets_the_companys_and_its_reps_send_with_it(client, world, member):
    r = _put(client, world.email("co-a"), "1 Title Plaza, Anytown, CA 90000")
    assert r.status_code == 200, r.text
    assert _row(world.a)[1] == "1 Title Plaza, Anytown, CA 90000"
    rep = _get(client, world.email("rep-a1"))
    assert rep["source"] == "company" and rep["in_use"] == "1 Title Plaza, Anytown, CA 90000"
    assert rep["company_name"] == "Seat Co A" and rep["can_edit"] is False


def test_a_member_and_an_inheriting_rep_cannot_set_it(client, world, member):
    assert _put(client, member["email"], "2 Nope Rd").status_code == 403
    r = _put(client, world.email("rep-a1"), "3 Nope Rd")
    assert r.status_code == 403 and "company" in r.json()["detail"]
    assert _row(world.a)[1] is None and _row(world.a1) is None


def test_one_account_never_sets_another_s(client, world):
    assert _put(client, world.email("co-a"), "1 Title Plaza").status_code == 200
    assert _row(world.b)[1] is None
    assert _get(client, world.email("co-b"))["source"] == "platform"
    assert _get(client, world.email("rep-b1"))["in_use"] == PLATFORM


def test_the_new_row_changes_nothing_else_about_a_regular_accounts_brand(client, world):
    from api.services.brand_resolver import resolve_brand
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        before = resolve_brand(cur, world.a1a)
    assert _put(client, world.email("ag-a1a"), "12 Oak Ave").status_code == 200
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        after = resolve_brand(cur, world.a1a)
    assert after == before
