"""
Redis connection utilities with proper SSL support for Upstash.
Handles ssl_cert_reqs parameter conversion from URL string to ssl module constants.
"""
import redis
import ssl
import urllib.parse


def create_redis_connection(redis_url):
    """
    Create a Redis connection with proper SSL configuration.
    
    When using Upstash Redis with TLS (rediss://), the URL may contain
    ?ssl_cert_reqs=CERT_REQUIRED which needs to be converted from a string
    to the actual ssl.CERT_REQUIRED constant.
    
    Args:
        redis_url: Redis connection URL (redis://, rediss://, or unix://)
    
    Returns:
        Redis client instance with proper SSL configuration
    
    Example:
        r = create_redis_connection("rediss://user:pass@host:6379?ssl_cert_reqs=CERT_REQUIRED")
    """
    # If URL contains ssl_cert_reqs parameter, we need to handle it specially
    if "ssl_cert_reqs=" in redis_url:
        # Remove the parameter from URL and parse it
        parsed = urllib.parse.urlparse(redis_url)
        params = urllib.parse.parse_qs(parsed.query)
        
        # Get the base URL without query parameters
        base_url = redis_url.split("?")[0]
        
        # Map string values to ssl module constants
        ssl_cert_reqs_map = {
            "CERT_REQUIRED": ssl.CERT_REQUIRED,
            "CERT_OPTIONAL": ssl.OPTIONAL,
            "CERT_NONE": ssl.CERT_NONE
        }
        
        cert_reqs_str = params.get("ssl_cert_reqs", ["CERT_REQUIRED"])[0]
        cert_reqs = ssl_cert_reqs_map.get(cert_reqs_str, ssl.CERT_REQUIRED)
        
        # Create connection with explicit SSL parameters
        return redis.from_url(base_url, ssl_cert_reqs=cert_reqs)
    else:
        # No SSL parameters, use URL as-is
        return redis.from_url(redis_url)

