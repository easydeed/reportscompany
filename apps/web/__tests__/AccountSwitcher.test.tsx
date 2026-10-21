/**
 * Tests for AccountSwitcher component
 * Phase T2.2: Frontend unit tests for multi-account UI
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AccountSwitcher } from '@/components/account-switcher';

/**
 * AccountSwitcher reads its data through `useAccounts()` (react-query), and
 * every test here rendered it bare — so all six died on "No QueryClient set"
 * before reaching an assertion. That is a gap in this file, not in the
 * product: the component is used in exactly one place, `app/app-layout.tsx`,
 * and `app/app/layout.tsx:58` wraps every route under /app in QueryProvider.
 *
 * `retry: false` so a rejected fetch surfaces immediately instead of being
 * retried three times past the waitFor, and a fresh client per render so one
 * test's cached accounts cannot answer the next test's query.
 */
function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

// Mock useToast
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

describe('AccountSwitcher', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // mockRESET, not mockClear. `clearAllMocks` and `mockClear` empty the
    // CALL LOG and leave the `mockResolvedValueOnce` QUEUE in place, so a
    // value queued by a test that ended early is handed to the next test's
    // first fetch. Three of the six failures here were that: each passes
    // alone and fails in the file, which is the signature.
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Single Account Scenario', () => {
    it('should render only account label when user has one account', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accounts: [
            {
              account_id: 'account-1',
              name: 'My Company',
              account_type: 'REGULAR',
              plan_slug: 'free',
              role: 'OWNER',
            },
          ],
          count: 1,
        }),
      });

      renderWithQuery(<AccountSwitcher />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByText('My Company')).toBeInTheDocument();
      });

      // Should NOT show dropdown trigger (ChevronDown icon)
      const dropdownButton = screen.queryByRole('button');
      expect(dropdownButton).not.toBeInTheDocument();
    });
  });

  describe('Multiple Accounts Scenario', () => {
    it('should render dropdown when user has multiple accounts', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          accounts: [
            {
              account_id: 'account-1',
              name: 'Primary Account',
              account_type: 'REGULAR',
              plan_slug: 'pro',
              role: 'OWNER',
            },
            {
              account_id: 'account-2',
              name: 'Secondary Account',
              account_type: 'REGULAR',
              plan_slug: 'free',
              role: 'MEMBER',
            },
          ],
          count: 2,
        }),
      });

      renderWithQuery(<AccountSwitcher />);

      await waitFor(() => {
        expect(screen.getByText('Primary Account')).toBeInTheDocument();
      });

      // Should show dropdown button
      const dropdownButton = screen.getByRole('button');
      expect(dropdownButton).toBeInTheDocument();
    });

    it('should call switch account API when selecting different account', async () => {
      // First fetch: get accounts
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accounts: [
              { account_id: 'account-1', name: 'Account One', account_type: 'REGULAR', plan_slug: 'free', role: 'OWNER' },
              { account_id: 'account-2', name: 'Account Two', account_type: 'REGULAR', plan_slug: 'pro', role: 'MEMBER' },
            ],
            count: 2,
          }),
        })
        // Second fetch: switch account
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ok: true }),
        });

      // Mock window.location.href
      delete (window as any).location;
      (window as any).location = { href: '' };

      renderWithQuery(<AccountSwitcher />);

      await waitFor(() => {
        expect(screen.getByText('Account One')).toBeInTheDocument();
      });

      // Open dropdown. userEvent, not fireEvent: Radix's trigger opens on
      // POINTER events, and `fireEvent.click` dispatches a bare MouseEvent,
      // so the menu never mounted and the item being clicked did not exist.
      const user = userEvent.setup();
      await user.click(screen.getByRole('button'));

      await waitFor(() => {
        expect(screen.getByText('Account Two')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Account Two'));

      // Verify API call
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/proxy/v1/account/use',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: 'account-2' }),
          })
        );
      });

      // Verify toast was called
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Account switched',
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('should show error toast when accounts fetch fails', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      renderWithQuery(<AccountSwitcher />);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error',
            description: 'Failed to load account information',
            variant: 'destructive',
          })
        );
      });
    });

    it('should show error toast when account switch fails', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            accounts: [
              { account_id: 'account-1', name: 'Account One', account_type: 'REGULAR', plan_slug: 'free', role: 'OWNER' },
              { account_id: 'account-2', name: 'Account Two', account_type: 'REGULAR', plan_slug: 'pro', role: 'MEMBER' },
            ],
            count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 403,
        });

      renderWithQuery(<AccountSwitcher />);

      await waitFor(() => {
        expect(screen.getByText('Account One')).toBeInTheDocument();
      });

      // Open dropdown and click — userEvent for the same reason as above.
      const user = userEvent.setup();
      await user.click(screen.getByRole('button'));
      await waitFor(() => screen.getByText('Account Two'));
      await user.click(screen.getByText('Account Two'));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error',
            description: 'Failed to switch account. Please try again.',
            variant: 'destructive',
          })
        );
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      (global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithQuery(<AccountSwitcher />);

      // Component should render but be in loading state
      // Exact loading UI depends on implementation
      expect(screen.queryByText('My Company')).not.toBeInTheDocument();
    });
  });
});

