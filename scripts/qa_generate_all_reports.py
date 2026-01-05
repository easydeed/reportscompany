#!/usr/bin/env python3
"""
QA Report Generator - Generate ALL report and email variations for QA review.

This script creates every combination of:
- Report types: New Listings, Market Update, Closed Sales
- Audiences: All Buyers, First-Time Buyer, Luxury, Investor, Condo, Family
- Cities: Configurable (default: Irvine, Los Angeles, San Diego)

Usage:
    python scripts/qa_generate_all_reports.py
    python scripts/qa_generate_all_reports.py --env staging
    python scripts/qa_generate_all_reports.py --cities "Irvine,La Verne" --lookback 30
    python scripts/qa_generate_all_reports.py --quick  # Just essential variations

Requirements:
    pip install requests python-dotenv
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    import requests
except ImportError:
    print("❌ Missing dependency. Run: pip install requests")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# API URLs
API_URLS = {
    "production": "https://api.trendyreports.io",
    "staging": "https://mr-api-staging.onrender.com",
    "local": "http://localhost:8000"
}

# Report types (after simplification)
REPORT_TYPES = {
    "new_listings": {
        "name": "New Listings Gallery",
        "report_type": "new_listings_gallery",
        "supports_audience": True
    },
    "market_update": {
        "name": "Market Update",
        "report_type": "market_snapshot",
        "supports_audience": False
    },
    "closed_sales": {
        "name": "Closed Sales",
        "report_type": "closed",
        "supports_audience": False
    }
}

# Audience presets (for New Listings only)
AUDIENCE_PRESETS = {
    "all": {
        "name": "All Buyers",
        "preset_key": None,
        "price_strategy": None
    },
    "first_time": {
        "name": "First-Time Buyer",
        "preset_key": "first_time_buyer",
        "price_strategy": {"mode": "relative_to_median", "value": 0.70, "position": "max"}
    },
    "luxury": {
        "name": "Luxury Buyer",
        "preset_key": "luxury_buyer",
        "price_strategy": {"mode": "relative_to_median", "value": 1.75, "position": "min"}
    },
    "investor": {
        "name": "Investor",
        "preset_key": "investor",
        "price_strategy": {"mode": "relative_to_median", "value": 0.85, "position": "max"}
    },
    "condo": {
        "name": "Condo Buyer",
        "preset_key": "condo_buyer",
        "price_strategy": None  # Uses property type filter instead
    },
    "family": {
        "name": "Family Buyer",
        "preset_key": "family_buyer",
        "price_strategy": {"mode": "relative_to_median", "value": 1.10, "position": "max"}
    }
}

# Test cities (SoCal / CRMLS coverage)
DEFAULT_CITIES = ["Irvine", "Los Angeles", "La Verne"]
QUICK_CITIES = ["Irvine"]

# Polling configuration
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 60  # 5 minutes max wait per report


@dataclass
class ReportResult:
    """Result of a report generation attempt."""
    report_type: str
    audience: str
    city: str
    lookback_days: int
    report_id: Optional[str] = None
    status: str = "pending"
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


class QAReportGenerator:
    def __init__(self, api_base_url: str, api_key: str, account_id: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.account_id = account_id
        self.results: List[ReportResult] = []
        
    def _headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Account-ID": self.account_id
        }
    
    def create_report(
        self,
        report_type: str,
        city: str,
        lookback_days: int = 30,
        audience_key: Optional[str] = None
    ) -> Optional[str]:
        """Create a report and return the report ID."""
        config = REPORT_TYPES.get(report_type)
        if not config:
            print(f"❌ Unknown report type: {report_type}")
            return None
        
        # Build filters
        filters = {}
        audience_name = "All"
        
        if audience_key and config["supports_audience"]:
            audience = AUDIENCE_PRESETS.get(audience_key, {})
            audience_name = audience.get("name", audience_key)
            
            if audience.get("preset_key"):
                filters["preset_key"] = audience["preset_key"]
                filters["preset_display_name"] = audience["name"]
            
            if audience.get("price_strategy"):
                filters["price_strategy"] = audience["price_strategy"]
        
        payload = {
            "report_type": config["report_type"],
            "city": city,
            "lookback_days": lookback_days,
            "filters": filters if filters else None
        }
        
        try:
            print(f"  📤 Creating: {config['name']} / {audience_name} / {city}...")
            resp = requests.post(
                f"{self.api_base_url}/reports",
                headers=self._headers(),
                json=payload,
                timeout=30
            )
            
            if resp.status_code in (200, 201, 202):
                data = resp.json()
                report_id = data.get("id") or data.get("report_id")
                print(f"     ✅ Created: {report_id}")
                return report_id
            else:
                print(f"     ❌ Failed ({resp.status_code}): {resp.text[:200]}")
                return None
                
        except requests.RequestException as e:
            print(f"     ❌ Request error: {e}")
            return None
    
    def poll_report(self, report_id: str) -> Dict:
        """Poll for report completion."""
        for attempt in range(MAX_POLL_ATTEMPTS):
            try:
                resp = requests.get(
                    f"{self.api_base_url}/reports/{report_id}",
                    headers=self._headers(),
                    timeout=30
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "unknown")
                    
                    if status == "completed":
                        return {
                            "status": "completed",
                            "pdf_url": data.get("pdf_url"),
                            "html_url": data.get("html_url") or f"{self.api_base_url}/reports/{report_id}/html"
                        }
                    elif status == "failed":
                        return {
                            "status": "failed",
                            "error": data.get("error_message", "Unknown error")
                        }
                    # Still processing
                    
            except requests.RequestException as e:
                print(f"     ⚠️ Poll error: {e}")
            
            time.sleep(POLL_INTERVAL_SECONDS)
        
        return {"status": "timeout", "error": "Exceeded max poll attempts"}
    
    def generate_variation(
        self,
        report_type: str,
        city: str,
        lookback_days: int,
        audience_key: Optional[str] = None
    ) -> ReportResult:
        """Generate a single report variation and wait for completion."""
        audience_name = "All"
        if audience_key:
            audience_name = AUDIENCE_PRESETS.get(audience_key, {}).get("name", audience_key)
        
        result = ReportResult(
            report_type=report_type,
            audience=audience_name,
            city=city,
            lookback_days=lookback_days
        )
        
        start_time = time.time()
        
        # Create the report
        report_id = self.create_report(report_type, city, lookback_days, audience_key)
        
        if not report_id:
            result.status = "create_failed"
            result.error = "Failed to create report"
            return result
        
        result.report_id = report_id
        
        # Poll for completion
        print(f"     ⏳ Waiting for completion...")
        poll_result = self.poll_report(report_id)
        
        result.status = poll_result.get("status", "unknown")
        result.pdf_url = poll_result.get("pdf_url")
        result.html_url = poll_result.get("html_url")
        result.error = poll_result.get("error")
        result.duration_seconds = time.time() - start_time
        
        if result.status == "completed":
            print(f"     ✅ Completed in {result.duration_seconds:.1f}s")
        else:
            print(f"     ❌ {result.status}: {result.error}")
        
        return result
    
    def generate_all(
        self,
        cities: List[str],
        lookback_days: int = 30,
        quick_mode: bool = False
    ) -> List[ReportResult]:
        """Generate all report variations."""
        print("\n" + "=" * 70)
        print("  TRENDY REPORTS - QA REPORT GENERATOR")
        print("=" * 70)
        print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Environment: {self.api_base_url}")
        print(f"  Cities: {', '.join(cities)}")
        print(f"  Lookback: {lookback_days} days")
        print(f"  Mode: {'Quick (essential only)' if quick_mode else 'Full (all variations)'}")
        print("=" * 70)
        
        total_count = 0
        
        for city in cities:
            print(f"\n📍 City: {city}")
            print("-" * 50)
            
            for report_key, report_config in REPORT_TYPES.items():
                print(f"\n  📊 {report_config['name']}")
                
                if report_config["supports_audience"]:
                    # Generate with each audience preset
                    audiences_to_test = ["all", "first_time", "luxury"] if quick_mode else list(AUDIENCE_PRESETS.keys())
                    
                    for audience_key in audiences_to_test:
                        result = self.generate_variation(
                            report_key, city, lookback_days, audience_key
                        )
                        self.results.append(result)
                        total_count += 1
                else:
                    # No audience filtering
                    result = self.generate_variation(
                        report_key, city, lookback_days, None
                    )
                    self.results.append(result)
                    total_count += 1
        
        print(f"\n\n{'=' * 70}")
        print(f"  GENERATION COMPLETE: {total_count} reports")
        print("=" * 70)
        
        return self.results
    
    def print_summary(self):
        """Print a summary of all results."""
        print("\n" + "=" * 70)
        print("  SUMMARY")
        print("=" * 70)
        
        completed = [r for r in self.results if r.status == "completed"]
        failed = [r for r in self.results if r.status != "completed"]
        
        print(f"\n  ✅ Completed: {len(completed)}")
        print(f"  ❌ Failed: {len(failed)}")
        
        if failed:
            print("\n  FAILURES:")
            for r in failed:
                print(f"    - {r.report_type} / {r.audience} / {r.city}: {r.error}")
        
        print("\n" + "-" * 70)
        print("  REPORT LINKS (for QA review):")
        print("-" * 70)
        
        for r in completed:
            print(f"\n  📄 {r.report_type.upper()} | {r.audience} | {r.city}")
            if r.pdf_url:
                print(f"     PDF: {r.pdf_url}")
            if r.html_url:
                print(f"     HTML: {r.html_url}")
    
    def export_results(self, filepath: str):
        """Export results to JSON for further analysis."""
        data = {
            "generated_at": datetime.now().isoformat(),
            "api_base_url": self.api_base_url,
            "total_reports": len(self.results),
            "completed": len([r for r in self.results if r.status == "completed"]),
            "failed": len([r for r in self.results if r.status != "completed"]),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n📁 Results exported to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Generate all report variations for QA")
    parser.add_argument(
        "--env",
        choices=["production", "staging", "local"],
        default="staging",
        help="Environment to use (default: staging)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        help="Override API URL"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key (or set QA_API_KEY env var)"
    )
    parser.add_argument(
        "--account-id",
        type=str,
        help="Account ID (or set QA_ACCOUNT_ID env var)"
    )
    parser.add_argument(
        "--cities",
        type=str,
        help="Comma-separated list of cities (default: Irvine,Los Angeles,La Verne)"
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=30,
        help="Lookback days (default: 30)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: only essential variations (1 city, 3 audiences)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="qa_results.json",
        help="Output file for results (default: qa_results.json)"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Get configuration
    api_url = args.api_url or API_URLS.get(args.env, API_URLS["staging"])
    api_key = args.api_key or os.getenv("QA_API_KEY") or os.getenv("API_KEY")
    account_id = args.account_id or os.getenv("QA_ACCOUNT_ID") or os.getenv("ACCOUNT_ID")
    
    if not api_key:
        print("❌ Missing API key. Set QA_API_KEY env var or use --api-key")
        print("\nTo get an API key:")
        print("  1. Log in to Trendy Reports")
        print("  2. Go to Settings → API")
        print("  3. Copy your API key")
        sys.exit(1)
    
    if not account_id:
        print("❌ Missing account ID. Set QA_ACCOUNT_ID env var or use --account-id")
        print("\nYou can find your account ID in the browser URL when logged in.")
        sys.exit(1)
    
    # Parse cities
    cities = QUICK_CITIES if args.quick else DEFAULT_CITIES
    if args.cities:
        cities = [c.strip() for c in args.cities.split(",")]
    
    # Create generator and run
    generator = QAReportGenerator(api_url, api_key, account_id)
    
    try:
        generator.generate_all(cities, args.lookback, quick_mode=args.quick)
        generator.print_summary()
        generator.export_results(args.output)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted. Partial results:")
        generator.print_summary()
        generator.export_results(args.output)


if __name__ == "__main__":
    main()
