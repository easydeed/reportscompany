"""
Image Proxy Utility for PDF Generation

MLS photo URLs often fail in PDFShift due to:
- Hotlinking protection
- Referrer checks  
- IP restrictions
- Authentication requirements

Solution: Fetch images from our server and convert to base64 data URIs.
This embeds the images directly in the HTML, ensuring they render in PDFShift.
"""

import base64
import httpx
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Timeout for image fetches (seconds)
IMAGE_FETCH_TIMEOUT = 10.0

# Max concurrent image fetches
MAX_CONCURRENT_FETCHES = 6

# User agent to avoid bot detection
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_image_as_base64(url: str) -> Optional[str]:
    """
    Fetch an image URL and convert to base64 data URI.
    
    Args:
        url: Image URL to fetch
        
    Returns:
        Base64 data URI string (e.g., "data:image/jpeg;base64,/9j/4AAQ...")
        or None if fetch fails
    """
    if not url:
        return None
    
    try:
        with httpx.Client(timeout=IMAGE_FETCH_TIMEOUT, follow_redirects=True) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "image/*",
                    "Referer": url,  # Some CDNs check referer
                }
            )
            
            if response.status_code != 200:
                print(f"⚠️  Image fetch failed ({response.status_code}): {url[:80]}...")
                return None
            
            # Detect content type
            content_type = response.headers.get("content-type", "image/jpeg")
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()
            
            # Ensure it's an image
            if not content_type.startswith("image/"):
                print(f"⚠️  Not an image ({content_type}): {url[:80]}...")
                return None
            
            # Convert to base64
            image_data = base64.b64encode(response.content).decode("utf-8")
            data_uri = f"data:{content_type};base64,{image_data}"
            
            print(f"✅ Image converted to base64 ({len(image_data)} chars): {url[:50]}...")
            return data_uri
            
    except httpx.TimeoutException:
        print(f"⏱️  Image fetch timeout: {url[:80]}...")
        return None
    except Exception as e:
        print(f"❌ Image fetch error: {e} - {url[:80]}...")
        return None


def convert_listings_photos_to_base64(listings: List[Dict], photo_key: str = "hero_photo_url") -> List[Dict]:
    """
    Convert all listing photos to base64 data URIs in parallel.
    
    This is the key function to call before storing gallery result_json.
    It replaces MLS photo URLs with embedded base64 data that PDFShift can render.
    
    Args:
        listings: List of listing dicts with photo URLs
        photo_key: Key containing the photo URL (default: "hero_photo_url")
        
    Returns:
        Updated listings with base64 data URIs (or None for failed fetches)
    """
    if not listings:
        return listings
    
    # Collect URLs to fetch
    urls_to_fetch = []
    url_to_idx = {}
    
    for idx, listing in enumerate(listings):
        url = listing.get(photo_key)
        if url and not url.startswith("data:"):  # Skip already-converted
            urls_to_fetch.append(url)
            url_to_idx[url] = idx
    
    if not urls_to_fetch:
        print("📷 No photos to convert (all empty or already base64)")
        return listings
    
    print(f"📷 Converting {len(urls_to_fetch)} photos to base64...")
    
    # Fetch images in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_FETCHES) as executor:
        future_to_url = {
            executor.submit(fetch_image_as_base64, url): url 
            for url in urls_to_fetch
        }
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                print(f"❌ Unexpected error for {url[:50]}...: {e}")
                results[url] = None
    
    # Update listings with base64 data
    success_count = 0
    for url, base64_data in results.items():
        idx = url_to_idx[url]
        if base64_data:
            listings[idx][photo_key] = base64_data
            success_count += 1
        else:
            # Keep original URL as fallback (template has "No Image" placeholder)
            pass
    
    print(f"📷 Photo conversion complete: {success_count}/{len(urls_to_fetch)} successful")
    return listings

