"""What the People page reads from /v1/company/reps and /agents, against a real
database, company A against company B.

  * `holds_seat` on a rep: the seat actions act on it, so it must be the open
    seat row — and must go false when the seat moves away;
  * `rep_id` on an agent (D-276): the page joins agents to reps by it;
  * neither list shows another company's reps or agents.

The world is `test_rep_seats.World`: A has two joined reps on seats and two
agents under A1; B has a joined rep with an agent and a pending rep.
"""
from test_rep_seats import (  # noqa: F401 — pytest fixtures, used by name
    _auth, _q, _reassign_body, client, sent, world,
)


def test_each_rep_says_whether_it_holds_a_seat(client, world):
    w = world
    reps = client.get("/v1/company/reps", headers=_auth(client, w.email("co-b"))).json()["reps"]
    by_id = {r["id"]: r for r in reps}
    assert by_id[w.b1]["holds_seat"] is True and by_id[w.b2]["holds_seat"] is True
    assert by_id[w.b2]["status"] == "pending"


def test_a_reassigned_rep_no_longer_holds_its_seat(client, world, sent):
    w = world
    headers = _auth(client, w.email("co-a"))
    resp = client.post(f"/v1/company/reps/{w.a1}/reassign", json=_reassign_body(w), headers=headers)
    assert resp.status_code == 200, resp.text
    reps = {r["id"]: r for r in client.get("/v1/company/reps", headers=headers).json()["reps"]}
    assert reps[w.a1]["holds_seat"] is False, "the leaving rep still offers seat actions"
    assert reps[resp.json()["new_rep_account_id"]]["holds_seat"] is True


def test_each_agent_carries_its_reps_id(client, world):
    w = world
    agents = client.get("/v1/company/agents", headers=_auth(client, w.email("co-a"))).json()["agents"]
    assert {(a["agent_id"], a["rep_id"]) for a in agents} == {(w.a1a, w.a1), (w.a1b, w.a1)}


def test_a_company_sees_only_its_own_people(client, world):
    w = world
    headers = _auth(client, w.email("co-a"))
    reps = client.get("/v1/company/reps", headers=headers)
    agents = client.get("/v1/company/agents", headers=headers)
    assert {r["id"] for r in reps.json()["reps"]} == {w.a1, w.a2}
    assert {a["rep_id"] for a in agents.json()["agents"]} <= {w.a1, w.a2}
    for text in (reps.text, agents.text):
        assert "SECRET" not in text and "PENDING" not in text and w.b1a not in text
