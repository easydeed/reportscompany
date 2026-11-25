"""Cancellable DNS for Stripe: no default-executor getaddrinfo survives the deadline."""
import ipaddress
import dns.asyncresolver
import dns.resolver
import httpx
from httpcore._backends.anyio import AnyIOBackend


class StripeBackend(AnyIOBackend):
    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        try:
            ipaddress.ip_address(host)
            address = host
        except ValueError:
            # The outer six-second request deadline covers both DNS families.
            try:
                answer = await dns.asyncresolver.resolve(host, 'A', lifetime=timeout or 2, search=False)
            except dns.resolver.NoAnswer:
                answer = await dns.asyncresolver.resolve(host, 'AAAA', lifetime=timeout or 2, search=False)
            address = answer[0].address
        # Connecting by literal avoids a second system DNS lookup. httpcore still
        # performs TLS with the ORIGINAL origin hostname and normal verification.
        return await super().connect_tcp(address, port, timeout, local_address, socket_options)


async def configure(transport):
    """Configure the SDK's dedicated HTTPX client; private hooks are held by tests."""
    old = transport._client_async
    context = old._transport._pool._ssl_context
    backend = httpx.AsyncHTTPTransport(verify=context, retries=0)
    backend._pool._network_backend = StripeBackend()
    transport._client_async = httpx.AsyncClient(transport=backend, trust_env=False)
    await old.aclose()
