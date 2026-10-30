"""Three sponsor-API leftovers that told the caller nothing (D-024, D-010, D-011).

* D-024: /v1/affiliate/all-reports and /all-schedules answered a non-rep with
  an empty 200, so "not a rep" read as "a rep with no agents". Every sibling
  refuses with 403 not_affiliate_account; these now do too.
* D-010: POST /v1/company/invite-rep accepted `office_location` and stored it
  nowhere, and every rep row carried `office: ""`. An unknown field is now a
  422 that names it, and the always-empty `office` is gone.
* D-011: /v1/company/metrics and its proxy were wired and called by nothing.
  Deleted; the dashboard reads /overview.
"""
from pathlib import Path

import pytest

from test_rep_seats import _auth, client, sent, world  # noqa: F401 — pytest fixtures, used by name

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("path", ["/v1/affiliate/all-reports", "/v1/affiliate/all-schedules"])
def test_a_non_rep_is_refused_like_every_sibling(client, world, path):
    resp = client.get(path, headers=_auth(client, world.email("co-a")))
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["error"] == "not_affiliate_account"


@pytest.mark.parametrize("path", ["/v1/affiliate/all-reports", "/v1/affiliate/all-schedules"])
def test_a_rep_still_reads_their_feed(client, world, path):
    """POSITIVE CONTROL."""
    assert client.get(path, headers=_auth(client, world.email("rep-a1"))).status_code == 200


def test_an_office_location_is_refused_not_dropped(client, world, sent):
    resp = client.post("/v1/company/invite-rep", headers=_auth(client, world.email("co-a")), json={
        "name": "Office Rep", "email": world.email("office-rep"), "first_name": "Office", "last_name": "Rep",
        "office_location": "Irvine",
    })
    assert resp.status_code == 422, resp.text
    assert "office_location" in resp.text
    assert sent == {"invites": [], "notices": []}


def test_no_rep_row_carries_an_office_that_is_always_empty(client, world):
    auth = _auth(client, world.email("co-a"))
    reps = client.get("/v1/company/reps", headers=auth).json()["reps"]
    overview = client.get("/v1/company/overview", headers=auth).json()["reps"]
    assert reps and overview
    assert not any("office" in r for r in reps + overview)


def test_the_unused_metrics_endpoint_is_gone(client, world):
    assert client.get("/v1/company/metrics", headers=_auth(client, world.email("co-a"))).status_code == 404
    assert not (ROOT / "apps/web/app/api/proxy/v1/company/metrics").exists()
