# Sponsor views — decisions for Jerry

Five calls. Each one changes what gets built; the recommendation is marked. Where the code and the build doc disagreed, the code won and the disagreement is listed here, not papered over.

## 1. Seats — what does the company pay for?
**The API has no seat.** `/v1/company/overview` counts reps and agents; the company's plan row carries market-report / schedule / property-report limits, not a rep count. "5 of 6 seats in use" — the renewal number at the top of the dashboard and the whole Plan page — cannot be computed today.
Options: (a) a `rep_seats` limit on the company plan row, so seats = plan limit and used = reps with `status ≠ deactivated`; (b) seats are just reps, and the Plan page lists reps without a cap.
**Recommended: (a).** It's one column and it is the thing Pacific Coast was buying. Until it lands the dashboard's first cell reads "Reps · 5" and the Plan page is blocked.

## 2. Leads — who sees them?
Agents' reports capture homeowner leads; they're stored; nobody above the agent sees them. The design has them behind a `leads` tweak (default on): a company headline count, a lead count on rep report rows and person stats, a notification toggle. No lead contact details on the rep side — the lead belongs to the agent.
Cost: two read fields on existing endpoints (README → "What the API doesn't return" #2). No new capture path.
**Recommended: yes.** "Your agents' reports brought in 23 homeowner leads this month" is the sentence that renews a contract.

## 3. Destructive rep actions — the consequence copy is now the code's, confirm it's what you want
Read from `routes/affiliates.py`:
- **deactivate** → `accounts.is_active = FALSE`. The agent is locked out entirely (and the pending invite link stops working). Drawn as "Pause their seat" / "Cancel the offer" with that stated. *Question:* is a lockout the intended effect of "pause", or should pause only block sending? If the latter, that's a new endpoint.
- **reactivate** → `is_active = TRUE`. Drawn as "Turn back on".
- **unsponsor** → `sponsor_account_id = NULL`, `sponsored_free → free`. The agent keeps the account and every report, on Free (3/month). **There is no re-sponsor endpoint** — the rep can't undo it. Drawn as "Take the seat back", red, with "You can't undo this from here." Only offered on paused seats, so it's always a two-step.
- The current company reps table shows Deactivate / Remove for reps with **no handler and no endpoint**. Not drawn. Do you want rep deactivation at all?

## 4. Rep-authored schedules — out
"The rep broadcasts the same reports to brokers and lenders the way agents do to homeowners" has no code behind it: `all-schedules` is a read of agents' schedules plus the rep's own, and the rep's own schedules come from the agent product the rep happens to also have. v4 makes Schedules read-only and removes New schedule. If Pacific Coast asked for rep broadcasting, say so and it becomes its own build; nothing in this package assumes it.

## 5. What does the rep still see of the agent product?
Today an affiliate's rail also carries the agent app (Dashboard · Market reports · Property reports · Schedules · Contacts · Branding · Plan & billing). v4's rail is four items. The rep's own reports still exist (they run them occasionally — inventory §6b) and show under "Mine" on the Reports feed; `/app/reports/new` stays reachable from there if you want a "Run a report" link. **Recommended:** keep the four-item rail; link "Run a report" from the Mine filter only; hide Branding / Plan & billing for company reps (they inherit; they don't pay).

## The one real datapoint
Pacific Coast Title used this surface and left. Everything above is reasoning; what they actually used and what they asked for overrides it. If anything they said is remembered — a number they wanted, a report they expected, a thing a rep couldn't do — it belongs at the top of this file.
