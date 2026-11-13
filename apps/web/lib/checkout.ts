// Whether the app may offer Upgrade / Stripe checkout to this account.
//
// The API decides (`account.checkout_available` on GET /v1/account/plan-usage,
// the same rule POST /v1/billing/checkout enforces). During the sponsored pilot
// it is false for sponsored agents. A response without the field (an older
// API mid-deploy) keeps today's behaviour; the API still refuses on its own.
export function checkoutOffered(usage: { account?: { checkout_available?: boolean } } | null | undefined): boolean {
  return usage?.account?.checkout_available !== false
}
