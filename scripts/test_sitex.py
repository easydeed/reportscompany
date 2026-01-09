import asyncio
import sys
import os
import logging

# Configure logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

# Add API source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from api.services.sitex import lookup_property

async def main():
    print("=" * 50)
    print("Testing SiteX Integration")
    print("=" * 50)
    
    # Test with known California address
    result = await lookup_property(
        address="714 Vine St",
        city_state_zip="Anaheim, CA 92805"
    )
    
    if result:
        print("\n[OK] SUCCESS!\n")
        print(f"  Address: {result.full_address}")
        print(f"  Street: {result.street}")
        print(f"  City: {result.city}, {result.state} {result.zip_code}")
        print(f"  County: {result.county}")
        print(f"  APN: {result.apn}")
        print(f"  FIPS: {result.fips}")
        print(f"  Owner: {result.owner_name}")
        print(f"  Beds/Baths: {result.bedrooms}/{result.bathrooms}")
        print(f"  SqFt: {result.sqft}")
        print(f"  Lot Size: {result.lot_size}")
        print(f"  Year Built: {result.year_built}")
        print(f"  Assessed Value: ${result.assessed_value:,}" if result.assessed_value else "  Assessed Value: N/A")
        print(f"  Legal: {result.legal_description[:80]}..." if result.legal_description and len(result.legal_description) > 80 else f"  Legal: {result.legal_description}")
    else:
        print("\n[FAIL] Property not found or error occurred")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
