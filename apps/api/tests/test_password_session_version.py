"""Replacement sessions survive a password change even within a single JWT second."""
import os
import uuid

import psycopg
import pytest

from api.auth import session_password_matches, sign_jwt, verify_jwt
from test_rep_seats import PASSWORD, _auth, client, world  # noqa: F401 - shared fixtures


def test_legacy_token_requires_issue_after_password_change():
    assert session_password_matches({"iat": 51}, "current", None, "test-secret")
    assert session_password_matches({"iat": 51}, "current", 50.75, "test-secret")
    assert not session_password_matches({"iat": 50}, "current", 50.75, "test-secret")


def test_versions_distinguish_sessions_issued_in_the_same_second(monkeypatch):
    import time
    issued = int(time.time())
    monkeypatch.setattr(time, "time", lambda: issued)
    secret = "session-version-unit-test-secret"
    old, new = [verify_jwt(sign_jwt({}, secret, password_hash=version), secret)
                for version in ("old-verifier", "new-verifier")]
    assert old["iat"] == new["iat"]
    assert not session_password_matches(old, "new-verifier", issued, secret)
    assert session_password_matches(new, "new-verifier", issued, secret)


@pytest.mark.parametrize("flow", ["change", "reset"])
def test_other_devices_expire_and_replacement_survives(client, world, flow):
    email = world.email("ag-a1a")
    previous = _auth(client, email)
    if flow == "change":
        result = client.post("/v1/users/me/password", headers=previous, json={
            "current_password": PASSWORD, "new_password": "NewPilotTest123!",
        })
    else:
        reset = str(uuid.uuid4())
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            conn.execute("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                SELECT id, %s, NOW() + INTERVAL '1 hour' FROM users WHERE email = %s
            """, (reset, email))
        result = client.post("/v1/auth/reset-password", json={
            "token": reset, "new_password": "NewPilotTest123!",
        })
    assert result.status_code == 200, result.text
    replacement = result.cookies.get("mr_token")
    assert replacement
    assert client.get("/v1/users/me", headers={"Authorization": f"Bearer {replacement}"}).status_code == 200
    assert client.get("/v1/users/me", headers=previous).status_code == 401
    client.cookies.clear()
    client.cookies.set("mr_token", previous["Authorization"].split(" ", 1)[1])
    try:
        assert client.get("/v1/users/me").status_code == 401
    finally:
        client.cookies.clear()
    login = client.post("/v1/auth/login", json={"email": email, "password": "NewPilotTest123!"})
    assert login.status_code == 200
    fresh = login.json()["access_token"]
    assert client.get("/v1/users/me", headers={"Authorization": f"Bearer {fresh}"}).status_code == 200
