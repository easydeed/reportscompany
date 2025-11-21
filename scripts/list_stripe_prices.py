#!/usr/bin/env python3
"""
Stripe Plan Sync Helper

Lists all active Stripe prices with their details.
Use this to discover price_ids and update your plans table.

Usage:
    STRIPE_SECRET_KEY=sk_test_... python scripts/list_stripe_prices.py

Output:
    price_id, product_name, nickname, amount, currency, interval

Then update your plans table:
    UPDATE plans SET stripe_price_id='price_abc123' WHERE plan_slug='pro';
"""

import os
import sys
import stripe


def main():
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    
    if not stripe_key:
        print("Error: STRIPE_SECRET_KEY environment variable not set", file=sys.stderr)
        print("Usage: STRIPE_SECRET_KEY=sk_test_... python scripts/list_stripe_prices.py", file=sys.stderr)
        sys.exit(1)
    
    stripe.api_key = stripe_key
    
    print("Fetching active Stripe prices...\n")
    print(f"{'Price ID':<30} {'Product':<25} {'Nickname':<25} {'Amount':<10} {'Currency':<10} {'Interval':<10}")
    print("=" * 120)
    
    try:
        prices = stripe.Price.list(limit=100, active=True, expand=["data.product"])
        
        for p in prices.auto_paging_iter():
            product = p.get("product")
            product_name = product.get("name") if isinstance(product, dict) else "N/A"
            nickname = p.get("nickname") or ""
            amount = p.get("unit_amount")
            currency = p.get("currency", "").upper()
            
            recurring = p.get("recurring")
            if recurring:
                interval = recurring.get("interval", "N/A")
                interval_count = recurring.get("interval_count", 1)
                interval_display = f"{interval_count} {interval}" if interval_count > 1 else interval
            else:
                interval_display = "one-time"
            
            # Format amount
            amount_display = f"${amount / 100:.2f}" if amount else "N/A"
            
            print(f"{p['id']:<30} {product_name:<25} {nickname:<25} {amount_display:<10} {currency:<10} {interval_display:<10}")
        
        print("\n" + "=" * 120)
        print("\nTo use these prices in your app:")
        print("1. Find the price_id for each plan (pro, team, affiliate)")
        print("2. Update your database:")
        print("   UPDATE plans SET stripe_price_id='price_abc123' WHERE plan_slug='pro';")
        print("3. Restart your API server to pick up the changes")
        
    except stripe.error.AuthenticationError:
        print("Error: Invalid Stripe API key", file=sys.stderr)
        sys.exit(1)
    except stripe.error.StripeError as e:
        print(f"Stripe API error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

