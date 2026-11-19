"""LR-007 defence in depth: the worker never fetches a private address for a render."""
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
    sent, routes = [], {}

    def handler(request):
        sent.append(str(request.url))
        status, headers, body = routes.get(str(request.url), (404, {}, b""))
        return httpx.Response(status, headers=headers, content=body)

    real_client = httpx.Client

    def client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(image_proxy.httpx, "Client", client)
    monkeypatch.setattr(image_proxy, "RETRY_DELAY", 0)
    return sent, routes


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
    sent, _ = network
    assert image_proxy.fetch_image_as_base64(url) is None
    assert sent == []


def test_a_public_listing_photo_still_embeds(network):
    sent, routes = network
    routes["https://photos.example.com/listing.png"] = (200, {"content-type": "image/png"}, IMAGE)
    out = image_proxy.fetch_image_as_base64("https://photos.example.com/listing.png")
    assert out and out.startswith("data:image/png;base64,")


def test_a_redirect_into_a_private_address_is_refused_at_that_hop(network):
    sent, routes = network
    routes["https://photos.example.com/hop.png"] = (302, {"location": "http://internal.example.com/secret"}, b"")
    assert image_proxy.fetch_image_as_base64("https://photos.example.com/hop.png") is None
    assert sent == ["https://photos.example.com/hop.png"]                # the private hop was never sent


def test_an_oversized_body_is_not_embedded(network, monkeypatch):
    sent, routes = network
    monkeypatch.setattr(image_proxy, "MAX_IMAGE_BYTES", 2000)
    routes["https://photos.example.com/huge.png"] = (200, {"content-type": "image/png"}, IMAGE)
    assert image_proxy.fetch_image_as_base64("https://photos.example.com/huge.png") is None
