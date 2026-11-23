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
  * ONE overall deadline for the whole fetch, enforced on the work itself
    (Codex #330, rounds 1 and 2). Not a timer on a caller waiting for a
    background thread: that only abandons the caller, and the abandoned work
    keeps a connection and a worker for as long as a server trickles bytes.
    Instead every step runs in the caller's own thread and is bounded by the
    time LEFT: the DNS lookup is a resolver query with that lifetime, and
    every socket connect, TLS handshake, read and write is given at most the
    remaining time (DeadlineBackend). A server that sends a header or body
    byte every few seconds is cut off at the deadline, the socket is closed,
    and nothing outlives the call;
  * the body capped while it streams.

It returns raw bytes; deciding whether they are an image is the caller's job
(services/upload.prepare_image). Refusals are FetchRefused with a short,
user-presentable reason.
"""
import ipaddress
import ssl
import time
from urllib.parse import urljoin, urlsplit

import httpcore
import httpx
from httpcore._backends.sync import SyncBackend

TIMEOUT_S = 10.0          # any single operation, and never past the deadline
MAX_REDIRECTS = 3
DEADLINE_S = 15.0         # the whole fetch, end to end
TOO_SLOW = "The link took too long to answer."

RESOLVER = None           # dns.resolver.Resolver; built on first use (tests may set one)


class FetchRefused(Exception):
    """The URL may not be fetched, or did not return a usable body."""


class _Deadline:
    def __init__(self, seconds: float):
        self.at = time.monotonic() + seconds

    def left(self) -> float:
        remaining = self.at - time.monotonic()
        if remaining <= 0:
            raise FetchRefused(TOO_SLOW)
        return remaining

    def bound(self, timeout) -> float:
        remaining = self.left()
        return remaining if timeout is None else min(timeout, remaining)


class _DeadlineStream(httpcore.NetworkStream):
    """Every socket operation gets at most the time left before the deadline."""

    def __init__(self, inner, deadline: _Deadline):
        self._inner, self._deadline = inner, deadline

    def _bound(self, timeout):
        try:
            return self._deadline.bound(timeout)
        except FetchRefused:
            raise httpcore.ReadTimeout(TOO_SLOW) from None

    def read(self, max_bytes, timeout=None):
        return self._inner.read(max_bytes, self._bound(timeout))

    def write(self, buffer, timeout=None):
        self._inner.write(buffer, self._bound(timeout))

    def close(self):
        self._inner.close()

    def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        tls = self._inner.start_tls(ssl_context, server_hostname, self._bound(timeout))
        return _DeadlineStream(tls, self._deadline)

    def get_extra_info(self, info):
        return self._inner.get_extra_info(info)


class _DeadlineBackend(SyncBackend):
    def __init__(self, deadline: _Deadline):
        self._deadline = deadline

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        try:
            timeout = self._deadline.bound(timeout)
        except FetchRefused:
            raise httpcore.ConnectTimeout(TOO_SLOW) from None
        stream = super().connect_tcp(host, port, timeout, local_address, socket_options)
        return _DeadlineStream(stream, self._deadline)


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def _lookup(host: str, lifetime: float) -> list[str]:
    """A and AAAA answers for `host`, the whole lookup within `lifetime` seconds.

    dnspython's lifetime is a real deadline for the query (retries and every
    nameserver included), unlike getaddrinfo, which cannot be bounded or
    interrupted from Python.
    """
    import dns.exception
    import dns.resolver

    global RESOLVER
    if RESOLVER is None:
        RESOLVER = dns.resolver.Resolver()
    started = time.monotonic()
    addresses = []
    for rdtype in ("A", "AAAA"):
        remaining = lifetime - (time.monotonic() - started)
        if remaining <= 0:
            raise FetchRefused(TOO_SLOW)
        try:
            answer = RESOLVER.resolve(host, rdtype, lifetime=remaining, search=False)
            addresses.extend(r.address for r in answer)
        except dns.resolver.NXDOMAIN as exc:
            raise FetchRefused("That address could not be found.") from exc
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            continue
        except dns.exception.Timeout as exc:
            raise FetchRefused(TOO_SLOW) from exc
        except dns.exception.DNSException as exc:
            raise FetchRefused("That address could not be found.") from exc
    return addresses


def _resolve(host: str, deadline: _Deadline) -> list[str]:
    try:
        ipaddress.ip_address(host)
        return [host]                                  # an IP literal: nothing to look up
    except ValueError:
        pass
    addresses = sorted(set(_lookup(host, deadline.left())))
    deadline.left()
    if not addresses:
        raise FetchRefused("That address could not be found.")
    return addresses


def _check(url: str, deadline: _Deadline) -> tuple[str, str, str]:
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
    addresses = _resolve(host, deadline)
    if not all(_is_public(a) for a in addresses):
        raise FetchRefused("That link points to a private or reserved network address.")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return host, addresses[0], path


def fetch(url: str, *, max_bytes: int, verify=True) -> bytes:
    """GET a public https URL with every hop checked, all within DEADLINE_S.

    `verify` is True (system trust) or an SSLContext, for tests only.
    """
    deadline = _Deadline(DEADLINE_S)
    context = verify if isinstance(verify, ssl.SSLContext) else httpx.create_ssl_context()
    with httpcore.ConnectionPool(ssl_context=context, network_backend=_DeadlineBackend(deadline),
                                 retries=0) as pool:
        for _hop in range(MAX_REDIRECTS + 1):
            host, address, path = _check(url, deadline)
            target = f"[{address}]" if ":" in address else address
            op = min(TIMEOUT_S, deadline.left())
            try:
                with pool.stream(
                    "GET", f"https://{target}{path}",
                    headers=[("Host", host), ("Accept", "image/*"),
                             ("User-Agent", "TrendyReports-image-import/1")],
                    extensions={"sni_hostname": host,
                                "timeout": {"connect": op, "read": op, "write": op, "pool": op}},
                ) as response:
                    headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in response.headers}
                    if response.status in (301, 302, 303, 307, 308):
                        location = headers.get("location")
                        if not location:
                            raise FetchRefused("The link redirected without saying where.")
                        url = urljoin(url, location)
                        continue
                    if response.status != 200:
                        raise FetchRefused(f"The link answered with HTTP {response.status}.")
                    declared = headers.get("content-length")
                    if declared and declared.isdigit() and int(declared) > max_bytes:
                        raise FetchRefused("The image at that link is too large.")
                    body = bytearray()
                    for chunk in response.iter_stream():
                        deadline.left()
                        body.extend(chunk)
                        if len(body) > max_bytes:
                            raise FetchRefused("The image at that link is too large.")
                    return bytes(body)
            except FetchRefused:
                raise
            except httpcore.TimeoutException as exc:
                raise FetchRefused(TOO_SLOW) from exc
            except (httpcore.ConnectError, httpcore.NetworkError, httpcore.ProtocolError,
                    httpcore.ProxyError, ssl.SSLError, OSError) as exc:
                raise FetchRefused("The link couldn't be fetched (connection or certificate problem).") from exc
    raise FetchRefused("The link redirected too many times.")
