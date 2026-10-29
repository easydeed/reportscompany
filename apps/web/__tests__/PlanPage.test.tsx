/**
 * `/account/plan` — the real page.
 *
 * WHAT THIS FILE USED TO BE (D-225)
 * ---------------------------------
 * Every test rendered `MockPlanPage`, a sketch of the page written inside
 * this file. `app/account/plan/page.tsx` was never imported, so eleven tests
 * could not fail because of anything in the product — and the sketch had
 * drifted from it in three ways that matter:
 *
 *   THE 0.8 WARNING THRESHOLD DOES NOT EXIST. The mock computed
 *   `usageRatio >= 0.8` in the browser and three tests asserted it. The page
 *   has no such rule: `PlanPageShell` renders Available / Approaching Limit /
 *   Limit Reached from `decision`, which the API decides. A client-side
 *   threshold was asserted for months against a server-side decision.
 *
 *   THE OVERRIDE WAS INVISIBLE. `limit` is
 *   `account.monthly_report_limit_override ?? plan.monthly_report_limit ?? 1`.
 *   The mock read `plan.monthly_report_limit` alone, so the per-account
 *   override — the thing a frozen or specially-provisioned account depends on
 *   — was never exercised.
 *
 *   THE SPONSORED BADGE NEEDS TWO CONDITIONS. The shell requires
 *   `sponsor_account_id !== null` AND `plan_slug === 'sponsored_free'`. The
 *   mock checked the slug alone, so it would show a badge where the product
 *   shows none.
 *
 * The mock is gone. These render the page, and `StripeBillingActions` is the
 * real component rather than a stand-in, because its slug rules were the
 * other thing the old file got wrong (it claimed a Manage Billing button for
 * every non-free slug; this page renders nothing for `starter` or `solo`).
 *
 * AND THE ROUTE IS AN ORPHAN (D-227), which is worth knowing before anyone
 * invests further in this file. NOTHING LINKS `/account/plan`: every Billing
 * entry in the sidebar points at `/app/settings/billing`, which carries its
 * own, fuller per-plan upgrade and downgrade flow. So the old suite was a
 * mock of a page no one can reach from inside the product. These tests are
 * still worth more than that mock — they describe real behaviour, including
 * three rules nothing else asserts — but if the route is deleted as a
 * duplicate, this file goes with it rather than being ported.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// The banner reads search params and is not what this file is about.
jest.mock('@/components/checkout-status-banner', () => ({
  CheckoutStatusBanner: () => <div data-testid="checkout-banner">Checkout Banner</div>,
}));

const PlanPage = require('../app/account/plan/page').default;

/** One response from `/v1/account/plan-usage`, shaped as the page reads it. */
function planUsage(over: Record<string, any> = {}) {
  return {
    account: {
      id: 'acct-1',
      name: 'Test Account',
      account_type: 'REGULAR',
      plan_slug: 'free',
      monthly_report_limit_override: null,
      sponsor_account_id: null,
      ...(over.account || {}),
    },
    plan: {
      plan_slug: 'free',
      plan_name: 'Free',
      monthly_report_limit: 3,
      allow_overage: false,
      overage_price_cents: null,
      ...(over.plan || {}),
    },
    usage: {
      report_count: 1,
      period_start: '2026-10-01',
      period_end: '2026-10-31',
      ...(over.usage || {}),
    },
    decision: over.decision ?? 'ALLOW',
    info: { ratio: 0.33, message: '', can_proceed: true, ...(over.info || {}) },
  };
}

/**
 * The plan name renders TWICE — as the card title and again in the "Current
 * Plan" cell below — so a bare getByText throws on "Growth". The title is
 * the one that identifies the plan at the top of the page, so assertions go
 * through here rather than through *AllBy*, which would pass if either copy
 * disappeared.
 */
function planTitle() {
  return document.querySelector('[data-slot="card-title"]');
}

function answerWith(body: any, ok = true) {
  (global.fetch as jest.Mock).mockResolvedValue({
    ok, status: ok ? 200 : 500, json: async () => body, text: async () => '',
  });
}

describe('Plan page — loading and failure', () => {
  it('shows the heading while it is still loading', () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<PlanPage />);
    expect(screen.getByText('Plan & Usage')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('says so when the request is refused', async () => {
    answerWith({}, false);
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load plan information')).toBeInTheDocument();
    });
  });

  it('says so when the request throws', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('offline'));
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load plan information')).toBeInTheDocument();
    });
  });
});

describe('Plan page — what it shows', () => {
  it('names the plan and counts reports against the limit', async () => {
    answerWith(planUsage({ plan: { plan_name: 'Growth', monthly_report_limit: 25 },
                           usage: { report_count: 20 } }));
    render(<PlanPage />);
    await waitFor(() => expect(planTitle()).toHaveTextContent('Growth'));
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('/ 25')).toBeInTheDocument();
  });

  it('prefers the account override to the plan limit', async () => {
    // Never exercised before. An override of 500 over a plan limit of 25 is
    // how a specially-provisioned account is served, and reading the plan
    // limit instead would under-report every one of them.
    answerWith(planUsage({
      account: { monthly_report_limit_override: 500 },
      plan: { monthly_report_limit: 25 },
      usage: { report_count: 20 },
    }));
    render(<PlanPage />);
    await waitFor(() => expect(screen.getByText('/ 500')).toBeInTheDocument());
    expect(screen.queryByText('/ 25')).not.toBeInTheDocument();
    expect(screen.getByText('4% used')).toBeInTheDocument();
  });
});

describe('Plan page — the decision comes from the API, not from a ratio', () => {
  it.each([
    ['ALLOW', 'Available'],
    ['ALLOW_WITH_WARNING', 'Approaching Limit'],
    ['BLOCK', 'Limit Reached'],
  ])('renders %s as "%s"', async (decision, label) => {
    answerWith(planUsage({ decision }));
    render(<PlanPage />);
    await waitFor(() => expect(screen.getByText(label)).toBeInTheDocument());
  });

  it('still says Available at 90% used when the API says ALLOW', async () => {
    // THE TEST THE OLD FILE GOT BACKWARDS. It asserted a client-side
    // `ratio >= 0.8` warning. There is no such rule: at 90% with a decision
    // of ALLOW the page says Available, because the server decides and the
    // page reports. If a threshold is ever wanted in the browser, this fails
    // and whoever adds it has to say so here.
    answerWith(planUsage({ plan: { monthly_report_limit: 100 },
                           usage: { report_count: 90 }, decision: 'ALLOW' }));
    render(<PlanPage />);
    await waitFor(() => expect(screen.getByText('90% used')).toBeInTheDocument());
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.queryByText('Approaching Limit')).not.toBeInTheDocument();
  });

  it('shows the API message when there is one', async () => {
    answerWith(planUsage({ decision: 'BLOCK',
                           info: { message: 'Monthly limit reached.' } }));
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByText('Monthly limit reached.')).toBeInTheDocument();
    });
  });
});

describe('Plan page — the sponsored badge needs both conditions', () => {
  it('shows Trial for a sponsored_free plan WITH a sponsor', async () => {
    answerWith(planUsage({
      account: { plan_slug: 'sponsored_free', sponsor_account_id: 'sponsor-1' },
      plan: { plan_slug: 'sponsored_free', plan_name: 'Trial' },
    }));
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByText('Trial plan provided by your affiliate partner'))
        .toBeInTheDocument();
    });
  });

  it('shows no badge for a sponsored_free plan with NO sponsor', async () => {
    // The old mock keyed on the slug alone and would have shown the badge
    // here. The shell requires `sponsor_account_id !== null` as well, and a
    // row with the slug but no sponsor is exactly the state a half-finished
    // affiliate link leaves behind.
    answerWith(planUsage({
      account: { plan_slug: 'sponsored_free', sponsor_account_id: null },
      plan: { plan_slug: 'sponsored_free', plan_name: 'Trial' },
    }));
    render(<PlanPage />);
    await waitFor(() => expect(planTitle()).toHaveTextContent('Trial'));
    expect(screen.queryByText('Trial plan provided by your affiliate partner'))
      .not.toBeInTheDocument();
  });
});

describe('Plan page — billing actions, with the real component', () => {
  it('offers both upgrades on free', async () => {
    answerWith(planUsage());
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Upgrade to Growth Plus/ })).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /Upgrade to Team/ })).toBeInTheDocument();
  });

  it('offers upgrades to a sponsored account too', async () => {
    // As of 2026-05-13 sponsored agents CAN self-upgrade: title companies
    // cannot pay for agent subscriptions (compliance), so agents pay their
    // own way.
    answerWith(planUsage({
      account: { plan_slug: 'sponsored_free', sponsor_account_id: 'sponsor-1' },
      plan: { plan_slug: 'sponsored_free', plan_name: 'Trial' },
    }));
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Upgrade to Growth Plus/ })).toBeInTheDocument();
    });
  });

  it('offers Manage Billing on a paid plan', async () => {
    answerWith(planUsage({ account: { plan_slug: 'pro' },
                           plan: { plan_slug: 'pro', plan_name: 'Growth Plus' } }));
    render(<PlanPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Manage Billing/ })).toBeInTheDocument();
    });
  });

  it('offers NOTHING on starter — which the old mock claimed a button for', async () => {
    // `StripeBillingActions` returns null for any slug that is not
    // free/sponsored_free/trial/pro/team — so `starter` (the Growth tier the
    // pricing page sells) and `solo` get nothing. That is a gap in THIS
    // page's copy of the billing UI, not in the product's: the sidebar's
    // Billing link goes to /app/settings/billing, which has its own
    // per-plan upgrade and downgrade flow. See the note at the top about
    // what that makes this route (D-227).
    answerWith(planUsage({ account: { plan_slug: 'starter' },
                           plan: { plan_slug: 'starter', plan_name: 'Growth' } }));
    render(<PlanPage />);
    await waitFor(() => expect(planTitle()).toHaveTextContent('Growth'));
    expect(screen.queryByRole('button', { name: /Upgrade/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Manage Billing/ })).not.toBeInTheDocument();
  });
});
