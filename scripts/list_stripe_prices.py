#!/usr/bin/env python3
"""
List active Stripe prices for plan configuration.

Usage:
    python scripts/list_stripe_prices.py

This script lists all active recurring Stripe prices to help map them to plan_slugs
in the plans table. Copy the price IDs and update your plans records accordingly.

Example output:
    Price ID                       | Product              | Nickname              | Amount  | Currency | Interval
    ------------------------------------------------------------------------------------------------
    price_1SO4sDBKYbtiKxfsUnKeJiox | Solo Agent           | Solo – $19/month      | $19.00  | usd      | month
    price_1STMtfBKYbtiKxfsqQ4r29Cw | Affiliate            | Affiliate – $99/month | $99.00  | usd      | month

Then update your database:
    UPDATE plans SET stripe_price_id = 'price_1SO4sDBKYbtiKxfsUnKeJiox' WHERE plan_slug = 'solo';
    UPDATE plans SET stripe_price_id = 'price_1STMtfBKYbtiKxfsqQ4r29Cw' WHERE plan_slug = 'affiliate';
"""

import os
import sys
import stripe

def main():
    # Get Stripe API key from environment
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    
    if not stripe_key:
        print("❌ Error: STRIPE_SECRET_KEY environment variable not set")
        print("\nUsage:")
        print("  export STRIPE_SECRET_KEY=sk_test_...")
        print("  python scripts/list_stripe_prices.py")
        sys.exit(1)
    
    stripe.api_key = stripe_key
    
    print("\n" + "="*120)
    print("Active Stripe Prices (Recurring)")
    print("="*120)
    print(f"{'Price ID':<35} | {'Product':<25} | {'Nickname':<25} | {'Amount':<8} | {'Currency':<8} | {'Interval':<10}")
    print("-"*120)
    
    try:
        # List all active recurring prices
        prices = stripe.Price.list(
            limit=100,
            active=True,
            expand=["data.product"],
            type="recurring"
        )
        
        found_count = 0
        
        for price in prices.auto_paging_iter():
            product = price.product
            product_name = product.name if hasattr(product, 'name') else str(product)
            nickname = price.get("nickname") or ""
            amount = price.unit_amount / 100 if price.unit_amount else 0
            currency = price.currency or ""
            interval = ""
            
            if price.recurring:
                interval = price.recurring.interval
                interval_count = price.recurring.interval_count
                if interval_count > 1:
                    interval = f"{interval_count} {interval}s"
            
            print(f"{price.id:<35} | {product_name:<25} | {nickname:<25} | ${amount:<7.2f} | {currency:<8} | {interval:<10}")
            found_count += 1
        
        print("-"*120)
        print(f"\nFound {found_count} active recurring price(s)")
        
        if found_count == 0:
            print("\n⚠️  No active recurring prices found in Stripe.")
            print("   Create prices in your Stripe Dashboard first:")
            print("   https://dashboard.stripe.com/prices")
        else:
            print("\n✅ To use these prices in your app:")
            print("   1. Choose the price_id for each plan (solo, affiliate, etc.)")
            print("   2. Update your database:")
            print("      UPDATE plans SET stripe_price_id = 'price_xxx' WHERE plan_slug = 'solo';")
            print("   3. Restart your API to pick up the changes")
            print("   4. Visit /app/billing to see the prices displayed")
        
        print("\n" + "="*120 + "\n")
        
    except stripe.error.AuthenticationError:
        print("\n❌ Authentication failed: Invalid Stripe API key")
        print("   Check that STRIPE_SECRET_KEY is correct")
        sys.exit(1)
    except stripe.error.StripeError as e:
        print(f"\n❌ Stripe API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
