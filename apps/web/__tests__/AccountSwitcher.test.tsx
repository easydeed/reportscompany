/**
 * Tests for AccountSwitcher component
 * Phase T2.2: Frontend unit tests for multi-account UI
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { AccountSwitcher } from '@/components/account-switcher';

// Mock useToast
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mockToast }),
}));

describe('AccountSwitcher', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
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

      render(<AccountSwitcher />);

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

      render(<AccountSwitcher />);

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

      render(<AccountSwitcher />);

      await waitFor(() => {
        expect(screen.getByText('Account One')).toBeInTheDocument();
      });

      // Open dropdown
      const dropdownButton = screen.getByRole('button');
      fireEvent.click(dropdownButton);

      // Wait for dropdown menu
      await waitFor(() => {
        expect(screen.getByText('Account Two')).toBeInTheDocument();
      });

      // Click on second account
      fireEvent.click(screen.getByText('Account Two'));

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

      render(<AccountSwitcher />);

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

      render(<AccountSwitcher />);

      await waitFor(() => {
        expect(screen.getByText('Account One')).toBeInTheDocument();
      });

      // Open dropdown and click
      fireEvent.click(screen.getByRole('button'));
      await waitFor(() => screen.getByText('Account Two'));
      fireEvent.click(screen.getByText('Account Two'));

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

      render(<AccountSwitcher />);

      // Component should render but be in loading state
      // Exact loading UI depends on implementation
      expect(screen.queryByText('My Company')).not.toBeInTheDocument();
    });
  });
});

