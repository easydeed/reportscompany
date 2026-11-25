"""Signed fixture requests only: no checkout, Stripe HTTP, or production DB."""
import hashlib
import hmac
import json
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from api.routes import stripe_webhook as route


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(route, 'STRIPE_SECRET_KEY', 'sk_test_fixture')
    monkeypatch.setattr(route, 'STRIPE_WEBHOOK_SECRET', 'whsec_fixture')
    app = FastAPI()
    app.include_router(route.router)
    return TestClient(app)


def post(client, *, mode=False, corrupt=False):
    body = json.dumps(dict(id='evt_fixture', type='price.created', livemode=mode,
                           created=int(time.time()), api_version='2025-10-29.clover')).encode()
    ts = str(int(time.time()))
    signature = hmac.new(b'whsec_fixture', ts.encode() + b'.' + body, hashlib.sha256).hexdigest()
    return client.post('/v1/webhooks/stripe', content=body,
                       headers={'stripe-signature': f't={ts},v1={"invalid" if corrupt else signature}'})


def test_original_signature_precedes_any_write(client, monkeypatch):
    calls = []
    monkeypatch.setattr(route, 'store_receipt', lambda e: calls.append(e))
    assert post(client, corrupt=True).status_code == 400
    assert calls == []


@pytest.mark.parametrize('stage', ['receipt', 'processing'])
def test_failure_returns_503_not_false_acknowledgement(client, monkeypatch, stage):
    calls = []
    def store(e):
        calls.append('receipt')
        if stage == 'receipt':
            raise RuntimeError('private database detail')
    def process(*a):
        calls.append('processing')
        raise RuntimeError('private database detail')
    monkeypatch.setattr(route, 'store_receipt', store)
    monkeypatch.setattr(route, 'process_receipt', process)
    response = post(client)
    assert response.status_code == 503
    assert 'private' not in response.text
    assert calls == (['receipt'] if stage == 'receipt' else ['receipt', 'processing'])


def test_verified_mode_mismatch_is_durably_quarantined(client, monkeypatch):
    saved = []
    monkeypatch.setattr(route, 'store_receipt', lambda e: saved.append(e))
    monkeypatch.setattr(route, 'process_receipt', lambda *a: None)
    assert post(client, mode=True).status_code == 200
    assert saved[0]['reason'] == 'mode_mismatch'


def test_unrecognised_config_returns_503_before_verification(client, monkeypatch):
    monkeypatch.setattr(route, 'STRIPE_SECRET_KEY', 'not_a_key')
    assert post(client).status_code == 503


def test_slow_processing_does_not_block_the_api_event_loop(client, monkeypatch):
    """Same ASGI event loop, offline: unrelated requests must not queue behind billing."""
    import asyncio
    import httpx
    import threading

    entered = threading.Event()
    calls = []
    monkeypatch.setattr(route, 'store_receipt', lambda e: calls.append('durable'))

    def slow_process(*args):
        assert calls == ['durable']
        entered.set()
        time.sleep(6.0)
        calls.append('processed')

    monkeypatch.setattr(route, 'process_receipt', slow_process)

    @client.app.get('/health')
    async def health():
        return {'ok': True}

    async def exercise():
        transport = httpx.ASGITransport(app=client.app)
        async with httpx.AsyncClient(transport=transport, base_url='http://offline') as ac:
            body = json.dumps(dict(id='evt_concurrency', type='price.created', livemode=False,
                                   created=int(time.time()), api_version='2025-10-29.clover')).encode()
            ts = str(int(time.time()))
            sig = hmac.new(b'whsec_fixture', ts.encode()+b'.'+body, hashlib.sha256).hexdigest()
            started = time.monotonic()
            webhook = asyncio.create_task(ac.post('/v1/webhooks/stripe', content=body,
                headers={'stripe-signature': f't={ts},v1={sig}'}))
            try:
                while not entered.is_set():
                    assert not webhook.done(), 'webhook ended before processing began'
                    assert time.monotonic() - started < 1.0
                    await asyncio.sleep(0.001)
                response = await ac.get('/health')
                assert response.status_code == 200
                assert time.monotonic() - started < 0.3
                assert not webhook.done()
            finally:
                result = await webhook
            assert result.status_code == 200
            assert calls == ['durable', 'processed']

    asyncio.run(exercise())
