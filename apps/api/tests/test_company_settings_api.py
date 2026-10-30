"""GET /v1/company/settings: the company's details and who is on the account.

Read by anyone on the account (D-280), for their own company only. The postal
address is read here and set through PUT /v1/account/postal-address (D-079) —
no company route writes it.
"""
import os
import uuid

import pytest

from test_rep_seats import PASSWORD, _auth, client, world  # noqa: F401 — pytest fixtures, used by name
from test_company_admin_role import member  # noqa: F401

psycopg = pytest.importorskip("psycopg")
DB_URL = os.getenv("DATABASE_URL")


def _settings(client, email):
    resp = client.get("/v1/company/settings", headers=_auth(client, email))
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_a_member_sees_everyone_on_their_company_and_who_can_act(client, world, member):
    s = _settings(client, member["email"])
    roles = {p["email"]: p["role"] for p in s["people"]}
    assert roles == {world.email("co-a"): "admin", member["email"]: "viewer"}
    assert s["people"][0]["role"] == "admin", "the admin is listed first"
    assert s["you"] == member["id"]
    assert s["can_manage"] is False
    assert _settings(client, world.email("co-a"))["can_manage"] is True


def test_another_companys_people_never_show(client, world, member):
    s = _settings(client, world.email("co-b"))
    emails = {p["email"] for p in s["people"]}
    assert emails == {world.email("co-b")}
    assert member["email"] not in str(s) and "Seat Co A" not in str(s)


def test_the_company_details_are_the_callers(client, world):
    with psycopg.connect(DB_URL) as conn:
        conn.execute("UPDATE affiliate_branding SET website_url = 'https://a.example', postal_address = '1 A St' "
                     "WHERE account_id = %s", (world.a,))
        conn.execute("UPDATE affiliate_branding SET website_url = 'https://b-secret.example' WHERE account_id = %s",
                     (world.b,))
    s = _settings(client, world.email("co-a"))
    assert s["company"] == {"name": "Seat Co A", "website_url": "https://a.example", "postal_address": "1 A St"}


def test_no_company_route_writes_the_postal_address():
    """One writer for the address: PUT /v1/account/postal-address (D-079),
    tested in test_postal_address_api.py. No company route writes it."""
    from api.routes import company
    import inspect
    src = inspect.getsource(company)
    assert "postal_address" in src, "the read is gone"
    assert not [l for l in src.splitlines() if "postal_address" in l and ("SET" in l or "INSERT" in l or "=" in l.split("postal_address")[0][-3:])]
    assert "postal_address" not in str(company.UpdateBrandingRequest.model_fields)
