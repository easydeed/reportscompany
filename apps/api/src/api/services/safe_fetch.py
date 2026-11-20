"""A guarded HTTPS fetch for user-supplied image URLs (LR-007, Jerry's option 1).

A pasted logo URL is fetched by our server, so the URL decides where our
server connects. Unguarded, that reaches anything the server can: cloud
metadata (169.254.169.254), localhost services, the private network. This
fetcher allows only what a public image needs:

  * https, port 443, no credentials in the URL;
  * a host whose every resolved address is public (one private or reserved
    answer refuses the whole request, so a mixed DNS reply cannot slip one
    through);
  * the connection is PINNED to the address that was checked, with TLS
    still verified against the hostname (SNI and certificate), so DNS that
    changes between the check and the connect cannot redirect it;
  * redirects followed by hand, each hop checked the same way, at most 3;
  * ONE overall deadline for the whole import (Codex #330 P2): DNS, connect,
    TLS, headers, every body chunk and every redirect hop share DEADLINE_S.
    HTTPX's timeouts are per operation (a server sending a byte every nine
    seconds never trips a 10 s read timeout), and getaddrinfo has no timeout
    at all, so the work runs on a small bounded pool and the caller stops
    waiting at the deadline. The abandoned work is told to stop (checked
    between chunks and after DNS) and each of its operations is bounded by
    TIMEOUT_S, so it cannot run on;
  * the body capped while it streams.

It returns raw bytes; deciding whether they are an image is the caller's job
(services/upload.prepare_image). Refusals are FetchRefused with a short,
user-presentable reason.
"""
import ipaddress
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from urllib.parse import urljoin, urlsplit

import httpx

TIMEOUT_S = 10.0          # any single operation (connect, one read), and never past the deadline
MAX_REDIRECTS = 3
DEADLINE_S = 15.0         # the whole fetch, end to end
TOO_SLOW = "The link took too long to answer."

# Bounded: imports stuck on a dead DNS server or a slow host cannot pile up
# threads. A request that waits for a free slot spends its own deadline.
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="safe-fetch")


class FetchRefused(Exception):
    """The URL may not be fetched, or did not return a usable body."""


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def _resolve(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as exc:
        raise FetchRefused("That address could not be found.") from exc
    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise FetchRefused("That address could not be found.")
    return addresses


def _check(url: str) -> tuple[str, str, str]:
    """(host, pinned address, path+query) for a URL we may fetch."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise FetchRefused("Only https:// image links can be imported.")
    if parts.username or parts.password:
        raise FetchRefused("Image links with a username or password can't be imported.")
    if parts.port not in (None, 443):
        raise FetchRefused("Image links must use the standard https port.")
    host = (parts.hostname or "").rstrip(".")
    if not host:
        raise FetchRefused("That isn't a complete link.")
    addresses = _resolve(host)
    if not all(_is_public(a) for a in addresses):
        raise FetchRefused("That link points to a private or reserved network address.")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return host, addresses[0], path


def fetch(url: str, *, max_bytes: int, verify=True) -> bytes:
    """GET a public https URL with every hop checked, within DEADLINE_S. `verify` is for tests only."""
    deadline = time.monotonic() + DEADLINE_S
    stop = threading.Event()
    future = _pool.submit(_fetch, url, max_bytes, verify, deadline, stop)
    try:
        return future.result(timeout=max(0.0, deadline - time.monotonic()))
    except FuturesTimeout:
        stop.set()               # the work stops at its next check; a queued one never starts
        future.cancel()
        raise FetchRefused(TOO_SLOW) from None


def _left(deadline: float, stop: threading.Event) -> float:
    remaining = deadline - time.monotonic()
    if stop.is_set() or remaining <= 0:
        raise FetchRefused(TOO_SLOW)
    return remaining


def _fetch(url: str, max_bytes: int, verify, deadline: float, stop: threading.Event) -> bytes:
    for _hop in range(MAX_REDIRECTS + 1):
        _left(deadline, stop)
        host, address, path = _check(url)
        target = f"[{address}]" if ":" in address else address
        timeout = min(TIMEOUT_S, _left(deadline, stop))
        try:
            with httpx.Client(timeout=timeout, verify=verify, follow_redirects=False, trust_env=False) as client:
                request = client.build_request(
                    "GET", f"https://{target}{path}",
                    headers={"Host": host, "Accept": "image/*", "User-Agent": "TrendyReports-image-import/1"},
                    extensions={"sni_hostname": host},
                )
                response = client.send(request, stream=True)
                try:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchRefused("The link redirected without saying where.")
                        url = urljoin(url, location)
                        continue
                    if response.status_code != 200:
                        raise FetchRefused(f"The link answered with HTTP {response.status_code}.")
                    declared = response.headers.get("content-length")
                    if declared and declared.isdigit() and int(declared) > max_bytes:
                        raise FetchRefused("The image at that link is too large.")
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        _left(deadline, stop)
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise FetchRefused("The image at that link is too large.")
                    return bytes(body)
                finally:
                    response.close()
        except FetchRefused:
            raise
        except httpx.TimeoutException as exc:
            raise FetchRefused(TOO_SLOW) from exc
        except httpx.HTTPError as exc:
            raise FetchRefused("The link couldn't be fetched (connection or certificate problem).") from exc
    raise FetchRefused("The link redirected too many times.")
