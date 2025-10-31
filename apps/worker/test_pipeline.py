#!/usr/bin/env python3
"""
Smoke test for compute pipeline: fetch → extract → validate → calculate
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from worker.vendors.simplyrets import build_market_snapshot_params, fetch_properties
from worker.compute.extract import PropertyDataExtractor
from worker.compute.validate import filter_valid
from worker.compute.calc import snapshot_metrics

print("\nTesting compute pipeline...")
print("=" * 60)

# Fetch data
print("\n1. Fetching properties from SimplyRETS...")
# Use simple query (demo API has limited support for date filters)
p = {"q": "Houston", "status": "Active"}
raw = fetch_properties(p, limit=80)
print(f"   raw: {len(raw)} properties fetched")

# Extract/normalize
print("\n2. Extracting and normalizing data...")
ext = PropertyDataExtractor(raw).run()
print(f"   extracted: {len(ext)} rows")

# Validate
print("\n3. Validating data...")
clean = filter_valid(ext)
print(f"   valid rows: {len(clean)}")

# Calculate metrics
print("\n4. Computing metrics...")
m = snapshot_metrics(clean)
print(f"   metrics computed successfully")

print("\n" + "=" * 60)
print("PIPELINE RESULTS:")
print("=" * 60)
print(f"\nRaw properties fetched: {len(raw)}")
print(f"Valid rows after extraction/validation: {len(clean)}")
print(f"Validation pass rate: {round(len(clean)/len(raw)*100 if raw else 0, 1)}%")

print("\nMetrics calculated:")
for key, value in m.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("Pipeline test complete!\n")

