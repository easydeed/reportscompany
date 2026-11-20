# Stripe live launch — Jerry's Dashboard checklist

Prepare the live catalog now; switch production billing only after LR-011–LR-014
are reviewed, merged and verified, before outreach. Jerry confirmed production
currently uses an `sk_test_` key. No live switch or purchase is authorized by
this checklist. **Jerry alone creates the live products and prices.**

1. **Open the correct Stripe account in live mode.** Resolve any account-activation
   requirements shown there. Check that you are outside the sandbox/test data.
   Live and test keys belong to different modes. [Stripe key guidance](https://docs.stripe.com/keys).
2. **In Product catalog, create or verify these live monthly recurring prices.**
   Do not create duplicates if they already exist; confirm the amount, currency
   and monthly interval. Record both live `price_…` IDs and product names.
   [Stripe product/price instructions](https://docs.stripe.com/products-prices/manage-prices).

   | App plan slug | Product name | Monthly price |
   |---|---|---:|
   | `starter` | Growth | USD 19 |
   | `pro` | Growth Plus | USD 29 |

3. **Locate the live server key on the API keys page.** Keep it in approved
   secret storage for `STRIPE_SECRET_KEY`; never paste it into chat, a ticket
   or a repository file. Do not replace the deployed test key yet.
   [Stripe API key handling](https://docs.stripe.com/keys).
4. **Prepare a live webhook destination in Workbench → Webhooks.** Its URL is
   `https://reportscompany.onrender.com/v1/webhooks/stripe`. Before enabling it,
   have Codex confirm the final LR-011–LR-014 event list and snapshot API version
   supported by the deployed handler. Current subscription handlers consume
   `customer.subscription.created`, `.updated` and `.deleted`; the billing fixes
   may add invoice events. Do not choose a thin payload for a snapshot handler.
   Store this endpoint's `whsec_…` as `STRIPE_WEBHOOK_SECRET` through the same
   secure handoff; it is separate from the API key and local CLI secret.
   [Stripe webhook setup](https://docs.stripe.com/webhooks).
5. **Hand off the two price IDs and configuration readiness.** Codex will map
   `plans.stripe_price_id` for `starter` and `pro` in a reviewed change. The active
   checkout reads that database mapping; changing old environment price maps
   alone is insufficient. Keys, prices and webhook must belong to the same live
   Stripe account. Leave production in test mode until the agreed release.
6. **At the approved launch, check delivery in Stripe.** Confirm the configured
   live webhook's deliveries succeed and the app records the correct plan and
   payment status. Any real-money verification purchase requires Jerry's explicit
   go-ahead. Codex verifies retry/duplicate safety and preserves test customer
   separation before lifting the temporary sponsored checkout pause.
