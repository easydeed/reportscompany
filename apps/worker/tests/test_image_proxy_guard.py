"""LR-007 defence in depth: the worker never fetches a private address for a render."""
import ipaddress
import socket
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from worker.utils import image_proxy  # noqa: E402

PUBLIC_IP = "93.184.216.34"
IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4000


@pytest.fixture
def network(monkeypatch):
    """Names resolve as listed; every request goes to a mock transport we record."""
    names = {"photos.example.com": PUBLIC_IP, "internal.example.com": "10.0.0.9"}
    real = socket.getaddrinfo

    def resolve(host, port, *args, **kwargs):
        if host in names:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (names[host], port))]
        return real(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    sent, routes, connected = [], {}, []

    def handler(request):
        # Keyed by what the request NAMES (scheme, Host, path); the URL itself carries the pinned IP.
        named = f"{request.url.scheme}://{request.headers['host']}{request.url.raw_path.decode()}"
        sent.append(named)
        connected.append(request.url.host)
        status, headers, body = routes.get(named, (404, {}, b""))
        return httpx.Response(status, headers=headers, content=body)

    real_client = httpx.Client

    def client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(image_proxy.httpx, "Client", client)
    monkeypatch.setattr(image_proxy, "RETRY_DELAY", 0)
    return sent, routes, connected


@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",
    "http://127.0.0.1:8099/v1/admin/ops/alerts",
    "http://localhost/x.png",
    "https://10.1.2.3/x.png",
    "https://[::1]/x.png",
    "https://internal.example.com/x.png",
    "file:///etc/passwd",
])
def test_private_and_non_http_targets_are_never_requested(network, url):
    sent, _, _ = network
    assert image_proxy.fetch_image_as_base64(url) is None
    assert sent == []


def test_a_public_listing_photo_still_embeds(network):
    sent, routes, _ = network
    routes["https://photos.example.com/listing.png"] = (200, {"content-type": "image/png"}, IMAGE)
    out = image_proxy.fetch_image_as_base64("https://photos.example.com/listing.png")
    assert out and out.startswith("data:image/png;base64,")
    assert network[2] == [PUBLIC_IP]                                   # connected to the checked address


def test_a_redirect_into_a_private_address_is_refused_at_that_hop(network):
    sent, routes, _ = network
    routes["https://photos.example.com/hop.png"] = (302, {"location": "http://internal.example.com/secret"}, b"")
    assert image_proxy.fetch_image_as_base64("https://photos.example.com/hop.png") is None
    assert sent == ["https://photos.example.com/hop.png"]                # the private hop was never sent


def test_an_oversized_body_is_not_embedded(network, monkeypatch):
    sent, routes, _ = network
    monkeypatch.setattr(image_proxy, "MAX_IMAGE_BYTES", 2000)
    routes["https://photos.example.com/huge.png"] = (200, {"content-type": "image/png"}, IMAGE)
    assert image_proxy.fetch_image_as_base64("https://photos.example.com/huge.png") is None


def test_a_name_that_rebinds_after_the_check_cannot_reach_the_private_address(monkeypatch):
    """Codex #330 P1: the check and the connection must use the SAME answer.

    rebind.example.com answers public for the first two lookups (what an
    admission check plus a request hook would see) and loopback after that.
    No real network: the connect itself is intercepted, recorded and refused.
    """
    import httpcore
    lookups = []
    real = socket.getaddrinfo

    def resolve(host, port, *args, **kwargs):
        if host == "rebind.example.com":
            lookups.append(host)
            address = PUBLIC_IP if len(lookups) <= 2 else "127.0.0.1"
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]
        return real(host, port, *args, **kwargs)

    reached = []

    def connect_tcp(self, host, port, *args, **kwargs):
        try:
            ipaddress.ip_address(host)
            reached.append(host)
        except ValueError:                       # handed a NAME: the socket would resolve it again
            reached.append(socket.getaddrinfo(host, port)[0][4][0])
        raise httpcore.ConnectError("intercepted: no real network in tests")

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setattr(httpcore._backends.sync.SyncBackend, "connect_tcp", connect_tcp)
    assert image_proxy.fetch_image_as_base64("https://rebind.example.com/photo.jpg") is None
    assert reached == [PUBLIC_IP]                # the checked address, never the rebound loopback
