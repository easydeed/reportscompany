# Stripe go-live checklist

## Jerry-confirmed live catalog IDs; PLANNED application mappings

| Plan | Monthly USD | Live price ID | Live product ID |
|---|---:|---|---|
| Growth (`starter`) | $19 | `price_1UddpFBa27XowvTp6siwCZ3Q` | `prod_VexkO3eDQhdlDr` |
| Growth Plus (`pro`) | $29 | `price_1UddpaBa27XowvTpqu8acKJP` | `prod_VexlkMlXRRVr9r` |

Jerry supplied these catalog IDs. The starter/pro application DB mappings
below are PLANNED go-live values, NOT a readout of current production. Codex
has not set them or identified a historical setter/time. This record is not
provider-side verification or permission to change anything. Jerry alone sets
configuration at go-live.

Target handoff after LR-014 removes the obsolete validator (current legacy
price-variable requirements are listed in the source inventory below):

| Host/service | Variable | Value at go-live |
|---|---|---|
| Vercel `reportscompany-web` | No Stripe variables | None: hosted Checkout is created by the API; no Stripe browser SDK/key is consumed. |
| Render `reportscompany-api` | `STRIPE_SECRET_KEY` | Existing live secret key, entered directly by Jerry; exact secret never printed/stored here. |
| Render `reportscompany-api` | `STRIPE_WEBHOOK_SECRET` | Signing secret for the live `/v1/webhooks/stripe` endpoint, entered directly by Jerry; never printed/stored here. |
| Render worker/ticker/bridge | No billing Stripe variables | None required by their current code. |

Price selection is **database configuration** on the active checkout/webhook
path, but checkout and portal still call the legacy configuration validator
which requires both price environment names below. Jerry's go-live DB mapping is:

- `plans.stripe_price_id` for `starter` -> `price_1UddpFBa27XowvTp6siwCZ3Q`.
- `plans.stripe_price_id` for `pro` -> `price_1UddpaBa27XowvTpqu8acKJP`.

The legacy map is not the active price source, but its validator is NOT dead:
`routes/billing.py` calls it for checkout and portal. Missing either legacy
price variable currently refuses both routes. LR-014 must remove the obsolete
Team requirement before go-live; do not invent a Team price or substitute
Growth's price merely to pass validation. Product IDs are references, not
consumed environment values.
The final LR-014 handoff must repeat the exact variable -> value list separately
for Vercel and Render, identify secrets to enter directly, and list these DB
mappings separately. No environment, database mapping, product, price or webhook
was changed while recording this checklist. No live payment tests.


### Stripe variable inventory (source verified; Render names supplied by Jerry)

Vercel production `reportscompany-web` was inspected read-only on November 19:
there are no Stripe-related variable names. The Render connector has no env-list
operation. Jerry supplied API names `STRIPE_PRICE_PRO_MONTH` and
`STRIPE_PRICE_TEAM_MONTH`, and reported no Stripe names on worker/ticker. This
is user-supplied inventory, not a connector inspection. `STRIPE_SECRET_KEY`
and `STRIPE_WEBHOOK_SECRET` were not included in that names-only reply; their
API/shared-group presence still needs confirmation. A live key was previously
confirmed, so do not infer its absence from this shorter list.

| Code-read variable | Purpose | Identifier expected | Slug | Status / exact nonsecret value |
|---|---|---|---|---|
| `STRIPE_SECRET_KEY` | API Stripe SDK and plan-catalog reads; LR-011 mode derivation | Live secret key, neither `prod_` nor `price_` | All | Required; Jerry enters actual secret directly. |
| `STRIPE_WEBHOOK_SECRET` | Verify original webhook bytes | Endpoint `whsec_` signing secret, neither ID type | All | Required; Jerry enters live endpoint secret directly. |
| `STRIPE_PRICE_PRO_MONTH` | Legacy pro map AND current checkout/portal configuration validation | `price_` | `pro` = Growth Plus | `price_1UddpaBa27XowvTpqu8acKJP` if retained; not the active price selector. |
| `STRIPE_PRICE_TEAM_MONTH` | Legacy team map AND current checkout/portal configuration validation | `price_` | Retired `team`, not `starter` or `pro` | Stale requirement; no approved value. LR-014 removes the requirement before go-live. |

No source-read Starter price environment variable exists. Starter/Growth uses
`plans.stripe_price_id = price_1UddpFBa27XowvTp6siwCZ3Q`; Pro/Growth Plus uses
`plans.stripe_price_id = price_1UddpaBa27XowvTpqu8acKJP`. Neither accepts a product
ID. The legacy lookup/reverse-lookup helper functions have no callers, but
`validate_stripe_config` does. Any extra deployed Stripe product/price names
must be checked against this list and marked unused, not assumed wired up.

Final go-live variable/value handoff remains conditional on the reviewed
LR-014 cleanup. Nobody has edited Vercel, Render, DB plan mappings or Stripe
configuration during this inventory. Actual secret values are not requested,
printed or stored in the checklist.


### Jerry-only go-live value list (do not apply during development)

- **Vercel `reportscompany-web`:** no Stripe variables to set.
- **Render API `STRIPE_SECRET_KEY`:** the existing live secret, entered directly
  by Jerry; actual value is intentionally not collected in chat.
- **Render API `STRIPE_WEBHOOK_SECRET`:** the live endpoint signing secret,
  entered directly by Jerry; actual value is intentionally not collected.
- **Render API `STRIPE_PRICE_PRO_MONTH`:**
  `price_1UddpaBa27XowvTpqu8acKJP` if LR-014 retains this legacy name.
- **Render API `STRIPE_PRICE_TEAM_MONTH`:** no approved value. It maps to retired
  `team`; LR-014 must remove the validator dependency before go-live. Do not
  assign the Starter/Growth price here to bypass it.
- **Worker/ticker:** no Stripe variables required or reported.
- **Separate DB mapping:** `starter` -> `price_1UddpFBa27XowvTp6siwCZ3Q`;
  `pro` -> `price_1UddpaBa27XowvTpqu8acKJP`. Product IDs are not price values.

All configured names Jerry reported are accounted for. Required secrets are
listed by name and purpose, not guessed values. Final instructions must match
the merged LR-014 code and confirm API/shared-group secret names first. No
configuration or DB mapping has been changed by this record.


## Verify current production values read-only

Run against mr-staging-db; this does not apply the planned values:

```sql
BEGIN READ ONLY;
SELECT plan_slug, is_active, stripe_price_id
FROM plans
WHERE plan_slug IN ('starter', 'pro')
ORDER BY plan_slug;
COMMIT;
```

Matching values would establish current configuration, not who set it or when.
That attribution needs audit/deployment evidence; it cannot be inferred from
this checklist or from Jerry supplying catalog IDs.

The Vercel product-ID variables Jerry mentions have not been located in the
inspected reportscompany-web scope. The older reportscompany project was not
accessible in the configured team. Product IDs have no web-app code consumer;
confirm the exact names/project and any integration/build use before deleting
those specific entries at go-live. Nothing was deleted or changed.
