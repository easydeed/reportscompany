/**
 * `/app/schedules/new` — the page, and the report types it offers.
 *
 * WHAT THIS FILE USED TO DO (D-212)
 * ---------------------------------
 * Five tests. The two that rendered anything mocked `next/dynamic` in order
 * to substitute a fake `ScheduleWizard` — but the page imports
 * `UnifiedReportWizard` STATICALLY and has since the wizard merge, so the
 * mock substituted nothing and `getByTestId('schedule-wizard')` looked for an
 * element that no longer exists. They failed for four months.
 *
 * The three that passed were of this shape:
 *
 *     const expectedReportTypes = ['market_snapshot', …, 'featured_listings'];
 *     expectedReportTypes.forEach(t => expect(expectedReportTypes).toContain(t));
 *
 * The array asserted against itself. `types.ts` was never imported and the
 * product was never involved, so they would have passed with the gallery
 * types deleted — which is the only thing they claimed to check.
 *
 * They read REPORT_TYPES now, and the page test renders the page.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@testing-library/jest-dom';
import { REPORT_TYPES } from '@/components/unified-wizard/types';

/** As `app/app/layout.tsx:58` mounts it. See AccountSwitcher.test.tsx. */
function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('New Schedule Page', () => {
  beforeEach(() => {
    // The wizard loads branding, profile and account on mount. None of them
    // is what this file is about, and the component already tolerates a
    // failed load, so they are answered with a 404 rather than fixtured.
    (global.fetch as jest.Mock).mockReset();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false, status: 404, json: async () => ({}), text: async () => '',
    });
  });

  it('renders the unified wizard, not a stand-in', async () => {
    const NewSchedulePage = require('../app/app/schedules/new/page').default;
    renderWithQuery(<NewSchedulePage />);

    // The wizard's own step rail. If the page is ever pointed at a different
    // component, these labels go and this fails — which is the thing the
    // mocked version could not notice.
    // Design's rail labels (Wizards v3): Report, Audience, Area & window, and
    // Schedule on this route. The step ids behind them are unchanged.
    const rail = await screen.findByRole('navigation', { name: 'Steps' });
    await waitFor(() => {
      expect(rail).toHaveTextContent('Report');
    });
    for (const label of ['Area & window', 'Schedule']) {
      expect(rail).toHaveTextContent(label);
    }

    // THREE, not four. `effectiveSteps = needsAudience ? [0,1,2,3] : [0,2,3]`
    // and no report type is chosen yet, so Audience is not in the rail. The
    // flow everyone describes as "our four-step wizard" opens on three, and
    // five of the eight report types never show the fourth. Asserted here
    // because a redesign measured against "four steps" is being measured
    // against something the product does not quite have.
    expect(rail).not.toHaveTextContent('Audience');
    expect(screen.getByText(/Step 1 of 3/)).toBeInTheDocument();
  });

  it('opens in schedule mode rather than send-now', async () => {
    const NewSchedulePage = require('../app/app/schedules/new/page').default;
    renderWithQuery(<NewSchedulePage />);
    await screen.findByRole('navigation', { name: 'Steps' });

    // `defaultMode="schedule"` is the only thing this route adds over
    // /app/reports/new, so it is the thing worth asserting about the route.
    const { UnifiedReportWizard } = require('@/components/unified-wizard');
    expect(UnifiedReportWizard).toBeDefined();
    const src = require('fs').readFileSync(
      require('path').join(__dirname, '../app/app/schedules/new/page.tsx'), 'utf8');
    expect(src).toContain('defaultMode="schedule"');
  });
});

describe('Report types offered by the wizard', () => {
  it('includes the two photo-driven gallery types', () => {
    const ids = REPORT_TYPES.map((r) => r.id);
    expect(ids).toContain('new_listings_gallery');
    expect(ids).toContain('featured_listings');
  });

  it('labels them for a reader rather than by slug', () => {
    const byId = Object.fromEntries(REPORT_TYPES.map((r) => [r.id, r]));
    expect(byId['new_listings_gallery'].title).toBe('New Listings Gallery');
    expect(byId['featured_listings'].title).toBe('Featured Listings');
  });

  it('keeps open_houses present but disabled', () => {
    // 3164cbb4 took Open Houses out of user-facing copy because SimplyRETS
    // open-house data is not reliably updated, and left the type wired. The
    // marketing site says seven; the wizard must therefore OFFER seven.
    const byId = Object.fromEntries(REPORT_TYPES.map((r) => [r.id, r]));
    expect(byId['open_houses'].disabled).toBe(true);
    expect(REPORT_TYPES.filter((r) => !r.disabled)).toHaveLength(7);
  });
});
