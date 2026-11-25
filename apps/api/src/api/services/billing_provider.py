"""LR-012 bounded authoritative reads. Only called in a worker thread or CLI."""
import asyncio
from collections.abc import Mapping
import time
import httpx
import stripe
from ..config.billing import STRIPE_SECRET_KEY
from .billing_envelope import normalize_verified_event, expected_live_mode
from .billing_network import configure

PROVIDER_SECONDS = 6


async def _request(operation, params):
    started = time.monotonic()
    transport = stripe.HTTPXClient(timeout=httpx.Timeout(2, connect=2, read=2, write=2, pool=1),
                                  allow_sync_methods=False)
    try:
        async with asyncio.timeout(max(0, PROVIDER_SECONDS - (time.monotonic()-started))):
            await configure(transport)
            client = stripe.StripeClient(STRIPE_SECRET_KEY, stripe_version='2025-10-29.clover',
                                         max_network_retries=0, http_client=transport)
            if operation == 'list':
                return await client.subscriptions.list_async(params)
            return await client.customers.create_async(params, options={
                'idempotency_key': 'billing-customer:' + params['metadata']['account_id']})
    finally:
        await transport.close_async()


def subscriptions(customer, live):
    if expected_live_mode(STRIPE_SECRET_KEY) != live:
        raise ValueError('billing_mode_mismatch')
    return asyncio.run(_request('list', {'customer': customer, 'status': 'all', 'limit': 10}))


def create_customer(email, account_id, account_name):
    result = asyncio.run(_request('create', {'email': email,
        'metadata': {'account_id': str(account_id), 'account_name': account_name}}))
    if not isinstance(result.get('id'), str) or not result['id'].startswith('cus_'):
        raise ValueError('invalid_customer_response')
    return result['id']


def choose_snapshot(inventory, e, current_subscription):
    """Return normalized allowlisted state or a deterministic review reason; never guess."""
    if not isinstance(inventory, Mapping):
        return None, 'subscription_inventory_incomplete'
    if inventory.get('has_more') is not False or not isinstance(inventory.get('data'), list):
        return None, 'subscription_inventory_incomplete'
    rows = inventory['data']
    if any(not isinstance(s, Mapping) for s in rows):
        return None, 'subscription_inventory_invalid'
    if any(s.get('customer') != e['customer_id'] or s.get('livemode') != e['livemode'] for s in rows):
        return None, 'provider_binding_mismatch'
    ongoing = [s for s in rows if s.get('status') not in ('canceled', 'incomplete_expired')]
    if len(ongoing) > 1:
        return None, 'multiple_subscriptions'
    selected = ongoing[0] if ongoing else next((s for s in rows
        if s.get('id') == (current_subscription or e['subscription_id'])), None)
    if selected is None:
        return None, 'subscription_missing'
    metadata = selected.get('metadata') or {}
    if not isinstance(metadata, Mapping):
        return None, 'provider_metadata_mismatch'
    if metadata.get('account_id') not in (None, e['account_id']):
        return None, 'provider_metadata_mismatch'
    # Inject only the already database-validated account binding; metadata alone never binds.
    obj = dict(selected); obj['metadata'] = {'account_id': e['account_id']}
    terminal = obj.get('status') in ('canceled', 'incomplete_expired')
    result = normalize_verified_event(dict(id=e['event_id'], created=e['created'],
        type='customer.subscription.deleted' if terminal else 'customer.subscription.updated',
        livemode=e['livemode'], data={'object': obj}), expected_live=e['livemode'])
    if result['reason']:
        return None, result['reason']
    cancel = obj.get('cancel_at_period_end', False)
    if type(cancel) is not bool or (cancel and not result['period_end']):
        return None, 'period_shape_unsupported'
    result['cancel_at_period_end'] = cancel
    return result, None
