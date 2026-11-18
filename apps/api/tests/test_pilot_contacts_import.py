import codecs
from contextlib import nullcontext
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import contacts


@pytest.mark.parametrize("prefix", [b"", codecs.BOM_UTF8])
def test_csv_upload_accepts_excel_headers(monkeypatch, prefix):
    app = FastAPI()

    @app.middleware("http")
    async def account(request, call_next):
        request.state.account_id = "00000000-0000-0000-0000-000000000001"
        return await call_next(request)

    app.include_router(contacts.router)
    cur = Mock()
    cur.fetchone.side_effect = [None, ("contact-id",)]
    monkeypatch.setattr(contacts, "db_conn", lambda: nullcontext((Mock(), cur)))
    monkeypatch.setattr(contacts, "set_rls", Mock())
    path = next(route.path for route in app.routes if route.path.endswith("/contacts/import"))
    data = prefix + b"name,email\r\nPat,pat@example.test\r\n"
    result = TestClient(app).post(path, files={"file": ("contacts.csv", data, "text/csv")})
    assert result.status_code == 200
    assert result.json()["created_contacts"] == 1
    assert result.json()["errors"] == []
