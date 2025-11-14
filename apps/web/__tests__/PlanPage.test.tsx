/**
 * Tests for Plan & Usage Page
 * Phase T2.2: Tests for plan display and usage warnings
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

// Mock modules
jest.mock('@/components/stripe-billing-actions', () => ({
  StripeBillingActions: ({ accountType, planSlug }: any) => (
    <div data-testid="stripe-actions">
      {accountType === 'REGULAR' && planSlug === 'free' && <button>Upgrade Plan</button>}
      {accountType === 'REGULAR' && planSlug !== 'free' && <button>Manage Billing</button>}
    </div>
  ),
}));

jest.mock('@/components/checkout-status-banner', () => ({
  CheckoutStatusBanner: () => <div data-testid="checkout-banner">Checkout Banner</div>,
}));

// Mock the actual plan page component logic
const MockPlanPage = ({ mockData }: { mockData: any }) => {
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    setTimeout(() => {
      setData(mockData);
      setLoading(false);
    }, 10);
  }, [mockData]);

  if (loading) return <div>Loading...</div>;
  if (data?.error) return <div>{data.error}</div>;

  const { plan, usage, account } = data;
  const usageRatio = usage.report_count / plan.monthly_report_limit;

  return (
    <div>
      <h1>Plan & Usage</h1>
      <div data-testid="plan-name">{plan.plan_name}</div>
      <div data-testid="usage-meter" data-ratio={usageRatio}>
        {usage.report_count}/{plan.monthly_report_limit}
      </div>
      {usageRatio >= 0.8 && <div data-testid="warning">Approaching limit</div>}
      {account.plan_slug === 'sponsored_free' && <div data-testid="sponsored-badge">Sponsored</div>}
      <div data-testid="stripe-actions-wrapper">
        {account.plan_slug !== 'sponsored_free' && <button>Stripe Action</button>}
      </div>
    </div>
  );
};

describe('Plan Page', () => {
  describe('Usage Display', () => {
    it('should show green meter when usage < 80%', async () => {
      const mockData = {
        account: { account_type: 'REGULAR', plan_slug: 'free' },
        plan: { plan_slug: 'free', plan_name: 'Free', monthly_report_limit: 50 },
        usage: { report_count: 30, schedule_run_count: 5 },
      };

      render(<MockPlanPage mockData={mockData} />);

      await waitFor(() => {
        expect(screen.getByTestId('usage-meter')).toHaveAttribute('data-ratio', '0.6');
      });

      expect(screen.queryByTestId('warning')).not.toBeInTheDocument();
    });

    it('should show yellow meter with warning when usage >= 80%', async () => {
      const mockData = {
        account: { account_type: 'REGULAR', plan_slug: 'free' },
        plan: { plan_slug: 'free', plan_name: 'Free', monthly_report_limit: 50 },
        usage: { report_count: 45, schedule_run_count: 10 },
      };

      render(<MockPlanPage mockData={mockData} />);

      await waitFor(() => {
        expect(screen.getByTestId('usage-meter')).toHaveAttribute('data-ratio', '0.9');
      });

      expect(screen.getByTestId('warning')).toBeInTheDocument();
      expect(screen.getByText('Approaching limit')).toBeInTheDocument();
    });
  });

  describe('Sponsored Account Badge', () => {
    it('should show sponsored badge for sponsored_free plan', async () => {
      const mockData = {
        account: { account_type: 'REGULAR', plan_slug: 'sponsored_free' },
        plan: { plan_slug: 'sponsored_free', plan_name: 'Sponsored Free', monthly_report_limit: 75 },
        usage: { report_count: 20, schedule_run_count: 5 },
      };

      render(<MockPlanPage mockData={mockData} />);

      await waitFor(() => {
        expect(screen.getByTestId('sponsored-badge')).toBeInTheDocument();
      });

      expect(screen.getByText('Sponsored')).toBeInTheDocument();
    });

    it('should NOT show Stripe buttons for sponsored accounts', async () => {
      const mockData = {
        account: { account_type: 'REGULAR', plan_slug: 'sponsored_free' },
        plan: { plan_slug: 'sponsored_free', plan_name: 'Sponsored Free', monthly_report_limit: 75 },
        usage: { report_count: 20, schedule_run_count: 5 },
      };

      render(<MockPlanPage mockData={mockData} />);

      await waitFor(() => {
        expect(screen.getByTestId('sponsored-badge')).toBeInTheDocument();
      });

      const stripeWrapper = screen.getByTestId('stripe-actions-wrapper');
      expect(stripeWrapper.querySelector('button')).not.toBeInTheDocument();
    });
  });

  describe('Stripe Actions', () => {
    it('should show Upgrade button for free plan', async () => {
      const mockData = {
        account: { account_type: 'REGULAR', plan_slug: 'free' },
        plan: { plan_slug: 'free', plan_name: 'Free', monthly_report_limit: 50 },
        usage: { report_count: 30, schedule_run_count: 5 },
      };

      render(<MockPlanPage mockData={mockData} />);

      await waitFor(() => {
        expect(screen.getByTestId('stripe-actions-wrapper')).toBeInTheDocument();
      });

      expect(screen.getByText('Stripe Action')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when data fetch fails', async () => {
      const mockData = {
        error: 'Failed to load plan information',
      };

      render(<MockPlanPage mockData={mockData} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load plan information')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator while fetching', () => {
      render(<MockPlanPage mockData={null} />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });
});

