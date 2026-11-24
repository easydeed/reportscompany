"""
Image Proxy Utility for PDF Generation

MLS photo URLs often fail in PDFShift due to:
- Hotlinking protection
- Referrer checks  
- IP restrictions
- Authentication requirements
- Rate limiting

Solution: Fetch images from our server and convert to base64 data URIs.
This embeds the images directly in the HTML, ensuring they render in PDFShift.

V2: Enhanced with retry logic, better headers, and rate limit handling.
"""

import base64
import ipaddress
import socket
import httpx
import time
from urllib.parse import urljoin, urlsplit
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timeout for image fetches (seconds)
IMAGE_FETCH_TIMEOUT = 15.0

# Max concurrent image fetches (reduced to avoid rate limits)
MAX_CONCURRENT_FETCHES = 3

# Delay between fetches to avoid rate limiting (seconds)
FETCH_DELAY = 0.5

# LR-007: a body larger than this is not an image we will embed.
MAX_IMAGE_BYTES = 15 * 1024 * 1024

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 1.0

# User agents to rotate (look like real browsers)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


MAX_REDIRECTS = 5


class _Refused(Exception):
    """The URL (or a redirect hop) points somewhere the worker must not connect."""


def _resolve_public(url: str):
    """(host, port, scheme, the ONE checked address) for a public http(s) URL, else raise _Refused.

    LR-007 defence in depth: never fetch a private, loopback, link-local or
    reserved address (cloud metadata, internal services) on the worker's
    behalf. Every resolved address must be public (one private answer refuses
    the host), and the caller connects to the returned address itself.
    """
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
            raise _Refused("not a public http(s) URL")
        port = parts.port or (443 if parts.scheme == "https" else 80)
        infos = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
        addresses = []
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                ip = ip.ipv4_mapped
            if not ip.is_global or ip.is_multicast:
                raise _Refused("private or reserved address")
            addresses.append(info[4][0])
        if not addresses:
            raise _Refused("no address")
        return parts.hostname.rstrip("."), port, parts.scheme, addresses[0]
    except (ValueError, OSError, UnicodeError) as exc:
        raise _Refused(type(exc).__name__) from exc


def _public_url(url: str) -> bool:
    try:
        _resolve_public(url)
        return True
    except _Refused:
        return False


def _pinned_get(client: httpx.Client, url: str, headers: dict) -> httpx.Response:
    """GET with redirects followed by hand, each hop CONNECTED to the address that was checked.

    Codex #330 P1: checking DNS and then handing HTTPX the hostname lets it
    resolve again, and a hostile name can answer public for the check and
    private for the connect. Here HTTPX is given the checked IP; the request
    still names the host (Host header) and TLS still verifies the certificate
    against the host name (SNI), so pinning weakens nothing.
    """
    for _hop in range(MAX_REDIRECTS + 1):
        host, port, scheme, address = _resolve_public(url)
        parts = urlsplit(url)
        target = f"[{address}]" if ":" in address else address
        default = (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
        path = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        request = client.build_request(
            "GET", f"{scheme}://{target}:{port}{path}",
            headers={**headers, "Host": host if default else f"{host}:{port}"},
            extensions={"sni_hostname": host} if scheme == "https" else {},
        )
        response = client.send(request)
        if response.is_redirect and response.headers.get("location"):
            url = urljoin(url, response.headers["location"])
            continue
        return response
    raise _Refused("too many redirects")


def fetch_image_as_base64(url: str, retry_count: int = 0) -> Optional[str]:
    """
    Fetch an image URL and convert to base64 data URI.
    
    V2: Enhanced with retry logic and better headers.
    
    Args:
        url: Image URL to fetch
        retry_count: Current retry attempt
        
    Returns:
        Base64 data URI string (e.g., "data:image/jpeg;base64,/9j/4AAQ...")
        or None if fetch fails
    """
    if not url:
        return None
    
    # Skip if already base64
    if url.startswith("data:"):
        return url

    if not _public_url(url):
        print(f"⛔ Refused (not a public address): {url[:60]}...")
        return None
    
    # Rotate user agent based on retry count
    user_agent = USER_AGENTS[retry_count % len(USER_AGENTS)]
    
    # Extract domain for referer
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"
    except:
        referer = url
    
    try:
        with httpx.Client(
            timeout=IMAGE_FETCH_TIMEOUT, 
            follow_redirects=False,    # followed by hand, every hop checked and pinned (_pinned_get)
            http2=False,  # Some CDNs have issues with HTTP/2
            trust_env=False,
        ) as client:
            response = _pinned_get(
                client,
                url,
                {
                    "User-Agent": user_agent,
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": referer,
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "cross-site",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
            
            if response.status_code == 429:
                # Rate limited - wait and retry
                if retry_count < MAX_RETRIES:
                    print(f"⏳ Rate limited, retrying in {RETRY_DELAY * (retry_count + 1)}s: {url[:60]}...")
                    time.sleep(RETRY_DELAY * (retry_count + 1))
                    return fetch_image_as_base64(url, retry_count + 1)
                print(f"⚠️  Rate limited (max retries): {url[:60]}...")
                return None
            
            if response.status_code == 403:
                # Forbidden - try with different headers on retry
                if retry_count < MAX_RETRIES:
                    print(f"🔄 403 Forbidden, retrying with different headers: {url[:60]}...")
                    time.sleep(RETRY_DELAY)
                    return fetch_image_as_base64(url, retry_count + 1)
                print(f"⚠️  403 Forbidden (max retries): {url[:60]}...")
                return None
            
            if response.status_code != 200:
                print(f"⚠️  Image fetch failed ({response.status_code}): {url[:60]}...")
                return None
            
            # Detect content type
            content_type = response.headers.get("content-type", "image/jpeg")
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()
            
            # Ensure it's an image
            if not content_type.startswith("image/"):
                print(f"⚠️  Not an image ({content_type}): {url[:60]}...")
                return None
            
            if len(response.content) > MAX_IMAGE_BYTES:
                print(f"⚠️  Image too large to embed ({len(response.content)//1024}KB): {url[:60]}...")
                return None

            # Convert to base64
            image_data = base64.b64encode(response.content).decode("utf-8")
            
            # Verify we got actual image data
            if len(response.content) < 1000:
                print(f"⚠️  Image too small ({len(response.content)} bytes), likely error page: {url[:60]}...")
                return None
            
            data_uri = f"data:{content_type};base64,{image_data}"
            
            print(f"✅ Image OK ({len(response.content)//1024}KB): {url[:50]}...")
            return data_uri
            
    except httpx.TimeoutException:
        if retry_count < MAX_RETRIES:
            print(f"⏱️  Timeout, retrying: {url[:60]}...")
            time.sleep(RETRY_DELAY)
            return fetch_image_as_base64(url, retry_count + 1)
        print(f"⏱️  Timeout (max retries): {url[:60]}...")
        return None
    except httpx.ConnectError as e:
        print(f"🔌 Connection error: {url[:60]}... - {e}")
        return None
    except Exception as e:
        print(f"❌ Image fetch error: {type(e).__name__}: {e} - {url[:60]}...")
        return None


def convert_listings_photos_to_base64(listings: List[Dict], photo_key: str = "hero_photo_url") -> List[Dict]:
    """
    Convert all listing photos to base64 data URIs.
    
    V2: Sequential processing with delays to avoid rate limits.
    While slower, this is more reliable for MLS CDNs that rate-limit aggressively.
    
    Args:
        listings: List of listing dicts with photo URLs
        photo_key: Key containing the photo URL (default: "hero_photo_url")
        
    Returns:
        Updated listings with base64 data URIs (or original URL for failed fetches)
    """
    if not listings:
        return listings
    
    # Collect URLs to fetch
    urls_to_process = []
    for idx, listing in enumerate(listings):
        url = listing.get(photo_key)
        if url and not url.startswith("data:"):  # Skip already-converted
            urls_to_process.append((idx, url))
    
    if not urls_to_process:
        print("📷 No photos to convert (all empty or already base64)")
        return listings
    
    print(f"📷 Converting {len(urls_to_process)} photos to base64 (sequential with {FETCH_DELAY}s delay)...")
    
    # Process sequentially with delays to avoid rate limiting
    success_count = 0
    for i, (idx, url) in enumerate(urls_to_process):
        # Add delay between requests (except first)
        if i > 0:
            time.sleep(FETCH_DELAY)
        
        try:
            base64_data = fetch_image_as_base64(url)
            if base64_data:
                listings[idx][photo_key] = base64_data
                success_count += 1
        except Exception as e:
            print(f"❌ Unexpected error processing {url[:50]}...: {e}")
    
    print(f"📷 Photo conversion complete: {success_count}/{len(urls_to_process)} successful")
    
    # Log summary for debugging
    if success_count == 0:
        print("⚠️  WARNING: No photos were converted! Check if MLS CDN is blocking requests.")
        print("⚠️  Common causes: IP blocking, rate limiting, missing referrer headers")
    elif success_count < len(urls_to_process):
        failed_count = len(urls_to_process) - success_count
        print(f"⚠️  {failed_count} photos failed to convert - will show placeholders in PDF")
    
    return listings
