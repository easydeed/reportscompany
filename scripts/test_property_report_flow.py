#!/usr/bin/env python3
"""
Property Report Flow Integration Test
======================================

Tests the full property report generation flow:
1. Search property via SiteX
2. Create property report
3. Poll for PDF generation
4. Verify public landing page

Usage:
    # Test against staging
    python scripts/test_property_report_flow.py --staging
    
    # Test against local API
    python scripts/test_property_report_flow.py --local
    
    # Direct service test (no HTTP, requires DB access)
    python scripts/test_property_report_flow.py --direct

Requirements:
    - API must be running (staging or local)
    - Valid auth token (will prompt or use TEST_AUTH_TOKEN env var)
    - SITEX_* environment variables configured
"""

import os
import sys
import time
import argparse
import json

# Load .env for local testing
from dotenv import load_dotenv
load_dotenv()

import httpx

# Test data
TEST_ADDRESS = "714 Vine St"
TEST_CITY_STATE_ZIP = "Anaheim, CA 92805"

# API URLs
STAGING_API_URL = "https://api-staging.trendyreports.io"
LOCAL_API_URL = "http://localhost:8000"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def ok(msg):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def fail(msg):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {msg}")

def info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def warn(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def header(msg):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")


class PropertyReportTester:
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.client = httpx.Client(timeout=60.0)
        
        self.headers = {
            "Content-Type": "application/json"
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    def close(self):
        self.client.close()
    
    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make authenticated request"""
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", {}).update(self.headers)
        return self.client.request(method, url, **kwargs)
    
    # =========================================================================
    # Test Steps
    # =========================================================================
    
    def test_health(self) -> bool:
        """Step 0: Verify API is healthy"""
        info("Checking API health...")
        try:
            resp = self.client.get(f"{self.base_url}/health")
            if resp.status_code == 200:
                ok(f"API is healthy: {self.base_url}")
                return True
            else:
                fail(f"Health check failed: {resp.status_code}")
                return False
        except Exception as e:
            fail(f"Cannot reach API: {e}")
            return False
    
    def test_property_search(self) -> dict:
        """Step 1: Search for property via SiteX"""
        info(f"Searching property: {TEST_ADDRESS}, {TEST_CITY_STATE_ZIP}")
        
        resp = self._request(
            "POST",
            "/v1/property/search",
            json={
                "address": TEST_ADDRESS,
                "city_state_zip": TEST_CITY_STATE_ZIP
            }
        )
        
        if resp.status_code == 401:
            fail("Authentication required. Set TEST_AUTH_TOKEN environment variable.")
            return None
        
        if resp.status_code != 200:
            fail(f"Property search failed: {resp.status_code} - {resp.text}")
            return None
        
        data = resp.json()
        
        if not data.get("success"):
            fail(f"Property not found: {data.get('error')}")
            if data.get("multiple_matches"):
                warn(f"Multiple matches found: {len(data['multiple_matches'])}")
                for m in data["multiple_matches"][:3]:
                    print(f"  - {m.get('address')}, APN: {m.get('apn')}")
            return None
        
        property_data = data.get("data", {})
        ok(f"Found property: {property_data.get('full_address') or property_data.get('street')}")
        print(f"    Owner: {property_data.get('owner_name', 'N/A')}")
        print(f"    APN: {property_data.get('apn', 'N/A')}")
        print(f"    County: {property_data.get('county', 'N/A')}")
        print(f"    Beds/Baths: {property_data.get('bedrooms')}/{property_data.get('bathrooms')}")
        
        return property_data
    
    def test_create_report(self, property_data: dict = None) -> dict:
        """Step 2: Create a property report"""
        info("Creating property report...")
        
        resp = self._request(
            "POST",
            "/v1/property/reports",
            json={
                "address": TEST_ADDRESS,
                "city_state_zip": TEST_CITY_STATE_ZIP,
                "report_type": "seller",
                "theme": 1,
                "accent_color": "#2563eb",
                "language": "en"
            }
        )
        
        if resp.status_code == 401:
            fail("Authentication required for report creation.")
            return None
        
        if resp.status_code == 429:
            warn(f"Rate limit or plan limit reached: {resp.json().get('detail')}")
            return None
        
        if resp.status_code not in (200, 201):
            fail(f"Report creation failed: {resp.status_code} - {resp.text}")
            return None
        
        report = resp.json()
        ok(f"Report created: {report.get('id')}")
        print(f"    Status: {report.get('status')}")
        print(f"    Short Code: {report.get('short_code')}")
        print(f"    QR Code URL: {report.get('qr_code_url', 'N/A')[:60]}...")
        
        return report
    
    def test_poll_report_status(self, report_id: str, max_wait: int = 120) -> dict:
        """Step 3: Poll for report completion"""
        info(f"Polling report status (max {max_wait}s)...")
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            resp = self._request("GET", f"/v1/property/reports/{report_id}")
            
            if resp.status_code != 200:
                fail(f"Failed to get report: {resp.status_code}")
                return None
            
            report = resp.json()
            status = report.get("status")
            
            if status != last_status:
                info(f"Status: {status}")
                last_status = status
            
            if status == "complete":
                elapsed = time.time() - start_time
                ok(f"Report complete in {elapsed:.1f}s")
                print(f"    PDF URL: {report.get('pdf_url', 'N/A')[:80]}...")
                return report
            
            if status == "failed":
                fail(f"Report generation failed")
                return report
            
            # Wait before next poll
            time.sleep(3)
        
        warn(f"Timeout waiting for report completion")
        return None
    
    def test_public_landing_page(self, short_code: str) -> dict:
        """Step 4: Test public landing page endpoint"""
        info(f"Testing public landing page: /v1/property/public/{short_code}")
        
        # This endpoint doesn't require auth
        resp = self.client.get(
            f"{self.base_url}/v1/property/public/{short_code}",
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 410:
            warn(f"Landing page inactive or expired: {resp.json().get('detail')}")
            return None
        
        if resp.status_code == 404:
            fail(f"Landing page not found")
            return None
        
        if resp.status_code != 200:
            fail(f"Landing page failed: {resp.status_code} - {resp.text}")
            return None
        
        data = resp.json()
        ok(f"Public landing page works!")
        print(f"    Address: {data.get('property_address')}, {data.get('property_city')}")
        print(f"    Agent: {data.get('agent_name', 'N/A')}")
        print(f"    Company: {data.get('company_name', 'N/A')}")
        print(f"    Theme Color: {data.get('accent_color')}")
        print(f"    Active: {data.get('is_active')}")
        
        return data
    
    def test_list_reports(self) -> list:
        """Bonus: List existing reports"""
        info("Listing property reports...")
        
        resp = self._request("GET", "/v1/property/reports?limit=5")
        
        if resp.status_code != 200:
            fail(f"List reports failed: {resp.status_code}")
            return []
        
        data = resp.json()
        reports = data.get("reports", [])
        total = data.get("total", 0)
        
        ok(f"Found {total} reports (showing {len(reports)})")
        for r in reports[:3]:
            print(f"    - [{r.get('status')}] {r.get('property_address')[:40]} ({r.get('short_code')})")
        
        return reports
    
    # =========================================================================
    # Full Flow
    # =========================================================================
    
    def run_full_test(self, skip_creation: bool = False):
        """Run the full integration test"""
        header("Property Report Integration Test")
        
        results = {
            "health": False,
            "search": False,
            "create": False,
            "poll": False,
            "public": False,
        }
        
        # Step 0: Health check
        if not self.test_health():
            return results
        results["health"] = True
        
        # Step 1: Property search
        property_data = self.test_property_search()
        if property_data:
            results["search"] = True
        else:
            warn("Continuing without property data...")
        
        # Step 2: Create report (or use existing)
        report = None
        if skip_creation:
            info("Skipping report creation, using existing reports...")
            reports = self.test_list_reports()
            if reports:
                report = {"id": reports[0]["id"], "short_code": reports[0]["short_code"]}
                results["create"] = True
        else:
            report = self.test_create_report(property_data)
            if report:
                results["create"] = True
        
        if not report:
            fail("No report available for testing")
            return results
        
        # Step 3: Poll for completion (skip if using existing complete report)
        if not skip_creation and report.get("status") != "complete":
            completed_report = self.test_poll_report_status(report["id"], max_wait=120)
            if completed_report and completed_report.get("status") == "complete":
                results["poll"] = True
                report = completed_report
        else:
            results["poll"] = True
        
        # Step 4: Test public landing page
        if report.get("short_code"):
            public_data = self.test_public_landing_page(report["short_code"])
            if public_data:
                results["public"] = True
        
        # Summary
        header("Test Results Summary")
        for test, passed in results.items():
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"  {test.ljust(15)}: {status}")
        
        all_passed = all(results.values())
        print()
        if all_passed:
            ok("All tests passed!")
        else:
            fail("Some tests failed")
        
        return results


def direct_service_test():
    """Test services directly without HTTP (requires local DB access)"""
    header("Direct Service Test (No HTTP)")
    
    # Add API path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))
    
    import asyncio
    from api.services.sitex import lookup_property
    
    async def test():
        info(f"Testing SiteX lookup: {TEST_ADDRESS}, {TEST_CITY_STATE_ZIP}")
        result = await lookup_property(TEST_ADDRESS, TEST_CITY_STATE_ZIP)
        
        if result:
            ok(f"Found: {result.full_address or result.street}")
            print(f"    Owner: {result.owner_name}")
            print(f"    APN: {result.apn}")
            print(f"    County: {result.county}")
            return True
        else:
            fail("Property not found")
            return False
    
    return asyncio.run(test())


def main():
    parser = argparse.ArgumentParser(description="Property Report Integration Test")
    parser.add_argument("--staging", action="store_true", help="Test against staging API")
    parser.add_argument("--local", action="store_true", help="Test against local API")
    parser.add_argument("--direct", action="store_true", help="Direct service test (no HTTP)")
    parser.add_argument("--skip-create", action="store_true", help="Skip report creation, use existing")
    parser.add_argument("--token", help="Auth token (or set TEST_AUTH_TOKEN env var)")
    parser.add_argument("--url", help="Custom API URL")
    args = parser.parse_args()
    
    # Direct service test
    if args.direct:
        success = direct_service_test()
        sys.exit(0 if success else 1)
    
    # Determine API URL
    if args.url:
        base_url = args.url
    elif args.staging:
        base_url = STAGING_API_URL
    elif args.local:
        base_url = LOCAL_API_URL
    else:
        # Default to local
        base_url = LOCAL_API_URL
        info("Defaulting to local API. Use --staging for staging.")
    
    # Get auth token
    auth_token = args.token or os.getenv("TEST_AUTH_TOKEN")
    
    if not auth_token:
        warn("No auth token provided. Some tests may fail.")
        warn("Set TEST_AUTH_TOKEN environment variable or use --token")
        print()
        # For public endpoint testing only
        auth_token = None
    
    # Run tests
    tester = PropertyReportTester(base_url, auth_token)
    try:
        results = tester.run_full_test(skip_creation=args.skip_create)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
    finally:
        tester.close()


if __name__ == "__main__":
    main()

