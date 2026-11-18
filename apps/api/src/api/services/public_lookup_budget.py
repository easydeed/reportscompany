"""LR-006 search budget. Default rollout mode: LOOKUP_BUDGET_ENFORCE=0.

Measure the November 12 policy before enabling refusals. A provider decision
corresponds to an actual outbound search attempt, including provider retries.
The counters are independent of customer records and account middleware.
"""
import asyncio
import hmac
import ipaddress
import logging
import math
import os
import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request

from .lookup_windows import Limits, LocalWindow, WindowResult, take_shared


logger = logging.getLogger("uvicorn.error.public_lookup_budget")
DIRECT = (("lb:v:direct", 20),)
_request_fallback = LocalWindow(4096)
_provider_fallback = LocalWindow(1)
_public_page: ContextVar[str | None] = ContextVar("public_lookup_page", default=None)


def _attribution_configured() -> bool:
    return (os.getenv("LOOKUP_TRUST_VERIFIED_PROXY") == "1"
            and bool(os.getenv("PROXY_SHARED_SECRET")) and bool(os.getenv("VISITOR_KEY_SECRET")))


if os.getenv("LOOKUP_BUDGET_ENFORCE") == "1" and not _attribution_configured():
    logger.warning("LOOKUP_BUDGET mode=observe reason=attribution_unconfigured")


def request_limits(request: "Request") -> Limits:
    """Use one shared direct bucket until an operator attests the web ingress."""
    if not _attribution_configured():
        return DIRECT

    headers = request.headers
    ts = headers.get("x-tr-proxy-ts", "")
    visitor = headers.get("x-tr-visitor-id", "")
    address = headers.get("x-tr-visitor-ip", "")
    signature = headers.get("x-tr-proxy-sig", "")
    if not (re.fullmatch("[0-9]{1,12}", ts) and abs(time.time() - int(ts)) <= 60
            and re.fullmatch("[0-9a-f]{32}", visitor)
            and re.fullmatch("[0-9a-f]{64}", signature)):
        return DIRECT
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return DIRECT
    if "%" in address:
        return DIRECT
    raw_path = request.scope.get("raw_path")
    path = raw_path.decode("ascii", "replace") if raw_path else request.scope["path"]
    message = f"{ts}\n{request.method} {path}\n{address}\n{visitor}"
    expected = hmac.digest(os.environ["PROXY_SHARED_SECRET"].encode(), message.encode(), "sha256").hex()
    if not hmac.compare_digest(signature, expected):
        return DIRECT

    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    network = str(ip) if ip.version == 4 else str(ipaddress.ip_network((ip, 64), strict=False))

    def key(value: str) -> str:
        return hmac.digest(os.environ["VISITOR_KEY_SECRET"].encode(), value.encode(), "sha256")[:16].hex()

    return ((f"lb:v:{key(visitor)}", 20), (f"lb:ip:{key(network)}", 60))


class LookupRefusal(Exception):
    def __init__(self, code: str, detail: str, headers: dict[str, str]):
        super().__init__(code)
        self.body = {"code": code, "detail": detail}
        self.headers = headers

    def response(self):
        from starlette.responses import JSONResponse

        return JSONResponse(status_code=429, content=self.body, headers=self.headers)


async def _check(stage: str, limits: Limits, fallback: LocalWindow, local_limits: Limits) -> dict[str, str]:
    # The shared Redis client is synchronous and configured with finite timeouts.
    try:
        result = await asyncio.to_thread(take_shared, limits)
        event = "LOOKUP_BUDGET"
    except Exception:
        event = "LOOKUP_LIMITER_DEGRADED"
        limits = local_limits
        try:
            result = fallback.take(limits)
        except Exception:
            # A broken fallback has no allowance. During observation the
            # application still returns its usual result.
            result = WindowResult(False, (), ())
    enforce = os.getenv("LOOKUP_BUDGET_ENFORCE", "0") == "1" and _attribution_configured()
    decision = "allow" if result.allowed else ("refuse" if enforce else "would-refuse")
    log = logger.warning if event == "LOOKUP_LIMITER_DEGRADED" else logger.info
    log("%s stage=%s decision=%s counts=%s", event, stage,
        decision, result.counts)
    if not enforce:
        return {}

    headers = {}
    wait = 60  # retry interval when the counter itself is unavailable
    if result.waits:
        # Display the tightest budget. When two budgets are exhausted, wait
        # until both have a free slot before inviting the visitor to retry.
        remaining = [max(0, limit - n) for (_, limit), n in zip(limits, result.counts)]
        index = min(range(len(limits)), key=lambda i: (remaining[i], -result.waits[i]))
        wait = result.waits[index]
        if stage != "provider":
            headers = {"RateLimit-Limit": str(limits[index][1]), "RateLimit-Remaining": str(remaining[index]),
                       "RateLimit-Reset": str(wait)}
    if result.allowed:
        return headers
    headers["Retry-After"] = str(wait)
    if stage != "provider" and result.waits:
        minutes = math.ceil(wait / 60)
        duration = "1 minute" if minutes == 1 else f"{minutes} minutes"
        raise LookupRefusal("lookup_limit", f"Too many searches from this device. Try again in {duration}.", headers)
    raise LookupRefusal("lookup_busy", "Search is busy right now. Try again in a few minutes.", headers)


async def check_request(request: "Request") -> dict[str, str]:
    limits = request_limits(request)
    return await _check("direct" if limits == DIRECT else "visitor_address", limits, _request_fallback, limits)


@contextmanager
def public_search(page_id: str):
    token = _public_page.set(page_id)
    try:
        yield
    finally:
        _public_page.reset(token)


async def check_provider_attempt():
    page_id = _public_page.get()
    if page_id is not None:
        await _check("provider", ((f"lb:p:{page_id}", 200), ("lb:g", 1000)),
                     _provider_fallback, (("lb:process", 30),))
