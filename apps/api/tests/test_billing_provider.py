"""Offline SDK boundary proofs: cancellation, zero retries, closed transport."""
import asyncio
import time
from types import SimpleNamespace
import pytest
from api.services import billing_provider as provider


def test_provider_timeout_cancels_and_closes_before_return(monkeypatch):
    calls={}
    class Transport:
        def __init__(self,**kw): calls['transport']=kw
        async def close_async(self): calls['closed']=True
    async def listing(params):
        calls['params']=params
        try: await asyncio.sleep(10)
        finally: calls['cancelled']=True
    def client(key,**kw):
        calls['client']=kw
        return SimpleNamespace(subscriptions=SimpleNamespace(list_async=listing))
    async def configure(transport): pass
    monkeypatch.setattr(provider,'configure',configure)
    monkeypatch.setattr(provider.stripe,'HTTPXClient',Transport)
    monkeypatch.setattr(provider.stripe,'StripeClient',client)
    monkeypatch.setattr(provider,'STRIPE_SECRET_KEY','sk_test_offline')
    monkeypatch.setattr(provider,'PROVIDER_SECONDS',.05)
    started=time.monotonic()
    with pytest.raises(TimeoutError): provider.subscriptions('cus_fixture',False)
    assert time.monotonic()-started<.5
    assert calls['cancelled'] and calls['closed']
    assert calls['client']['max_network_retries']==0
    assert calls['client']['stripe_version']=='2025-10-29.clover'
    assert calls['params']=={'customer':'cus_fixture','status':'all','limit':10}
    assert not calls['transport']['allow_sync_methods']


def test_mode_mismatch_never_calls_provider(monkeypatch):
    monkeypatch.setattr(provider,'STRIPE_SECRET_KEY','sk_test_offline')
    monkeypatch.setattr(provider,'_request',lambda *a:pytest.fail('unexpected provider call'))
    with pytest.raises(ValueError,match='mode_mismatch'): provider.subscriptions('cus_fixture',True)


@pytest.mark.parametrize('inventory,reason', [
    (None,'subscription_inventory_incomplete'),
    ({'has_more':False,'data':[None]},'subscription_inventory_invalid'),
    ({'has_more':True,'data':[]},'subscription_inventory_incomplete'),
])
def test_malformed_inventory_is_a_review_case(inventory,reason):
    assert provider.choose_snapshot(inventory,{},None)==(None,reason)


def test_stripe_dns_cancellation_never_uses_system_resolver(monkeypatch):
    import socket
    import dns.asyncresolver
    from api.services.billing_network import StripeBackend
    from httpcore._backends.anyio import AnyIOBackend
    state={}
    async def slow(*args,**kwargs):
        state['lifetime']=kwargs['lifetime']
        try: await asyncio.sleep(10)
        finally: state['cancelled']=True
    monkeypatch.setattr(dns.asyncresolver,'resolve',slow)
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:pytest.fail('system DNS escaped deadline'))
    async def run():
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(.05):
                await StripeBackend().connect_tcp('api.stripe.com',443,timeout=2)
    started=time.monotonic();asyncio.run(run())
    assert time.monotonic()-started<.5 and state['cancelled']
    assert state['lifetime']==2


def test_sdk_transport_is_wired_to_bounded_dns_with_tls_verification():
    import stripe
    from api.services.billing_network import configure,StripeBackend
    async def run():
        transport=stripe.HTTPXClient(timeout=2,allow_sync_methods=False)
        try:
            await configure(transport)
            pool=transport._client_async._transport._pool
            assert isinstance(pool._network_backend,StripeBackend)
            assert pool._ssl_context.check_hostname
            assert not transport._client_async._trust_env
        finally: await transport.close_async()
    asyncio.run(run())


def test_customer_create_uses_stable_account_key_and_closes_transport(monkeypatch):
    calls={}
    class Transport:
        def __init__(self,**kw): pass
        async def close_async(self): calls['closed']=True
    async def configure(transport): pass
    async def create(params,options):
        calls.update(params=params,options=options)
        return {'id':'cus_fixture'}
    monkeypatch.setattr(provider,'configure',configure)
    monkeypatch.setattr(provider.stripe,'HTTPXClient',Transport)
    monkeypatch.setattr(provider.stripe,'StripeClient',lambda *a,**k:
        SimpleNamespace(customers=SimpleNamespace(create_async=create)))
    assert provider.create_customer('fixture@example.com','account-fixture','Fixture')=='cus_fixture'
    assert calls['options']=={'idempotency_key':'billing-customer:account-fixture'}
    assert calls['closed']
