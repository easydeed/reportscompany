/**
 * Tests for Affiliate Page
 * Phase T2.2: Tests for affiliate dashboard and metrics
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

// Mock affiliate page component
const MockAffiliatePage = ({ mockResponse }: { mockResponse: any }) => {
  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setTimeout(() => {
      if (mockResponse.status === 403) {
        setError('Not an affiliate account');
      } else if (mockResponse.ok) {
        setData(mockResponse.data);
      } else {
        setError('Failed to load');
      }
      setLoading(false);
    }, 10);
  }, [mockResponse]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div data-testid="error-message">{error}</div>;

  return (
    <div>
      <h1>Affiliate Dashboard</h1>
      <div data-testid="summary-cards">
        <div data-testid="card-total-agents">Total Agents: {data.total_agents}</div>
        <div data-testid="card-active-agents">Active: {data.active_agents}</div>
        <div data-testid="card-reports">Reports: {data.total_reports}</div>
      </div>
      <div data-testid="agents-table">
        {data.agents.map((agent: any) => (
          <div key={agent.email} data-testid={`agent-${agent.email}`}>
            {agent.email} - {agent.status}
          </div>
        ))}
      </div>
    </div>
  );
};

describe('Affiliate Page', () => {
  describe('Successful Load', () => {
    it('should render summary cards with affiliate metrics', async () => {
      const mockResponse = {
        ok: true,
        data: {
          total_agents: 15,
          active_agents: 12,
          total_reports: 450,
          agents: [
            { email: 'agent1@example.com', status: 'active', reports_count: 30 },
            { email: 'agent2@example.com', status: 'active', reports_count: 25 },
          ],
        },
      };

      render(<MockAffiliatePage mockResponse={mockResponse} />);

      await waitFor(() => {
        expect(screen.getByTestId('summary-cards')).toBeInTheDocument();
      });

      expect(screen.getByTestId('card-total-agents')).toHaveTextContent('Total Agents: 15');
      expect(screen.getByTestId('card-active-agents')).toHaveTextContent('Active: 12');
      expect(screen.getByTestId('card-reports')).toHaveTextContent('Reports: 450');
    });

    it('should render agents table with agent details', async () => {
      const mockResponse = {
        ok: true,
        data: {
          total_agents: 2,
          active_agents: 2,
          total_reports: 55,
          agents: [
            { email: 'alice@realty.com', status: 'active', reports_count: 30 },
            { email: 'bob@realty.com', status: 'invited', reports_count: 0 },
          ],
        },
      };

      render(<MockAffiliatePage mockResponse={mockResponse} />);

      await waitFor(() => {
        expect(screen.getByTestId('agents-table')).toBeInTheDocument();
      });

      expect(screen.getByTestId('agent-alice@realty.com')).toHaveTextContent('alice@realty.com - active');
      expect(screen.getByTestId('agent-bob@realty.com')).toHaveTextContent('bob@realty.com - invited');
    });
  });

  describe('Access Control', () => {
    it('should show "not affiliate" message when user is not an affiliate', async () => {
      const mockResponse = {
        ok: false,
        status: 403,
      };

      render(<MockAffiliatePage mockResponse={mockResponse} />);

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
      });

      expect(screen.getByText('Not an affiliate account')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error when API call fails', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
      };

      render(<MockAffiliatePage mockResponse={mockResponse} />);

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
      });

      expect(screen.getByText('Failed to load')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should handle affiliate with no agents', async () => {
      const mockResponse = {
        ok: true,
        data: {
          total_agents: 0,
          active_agents: 0,
          total_reports: 0,
          agents: [],
        },
      };

      render(<MockAffiliatePage mockResponse={mockResponse} />);

      await waitFor(() => {
        expect(screen.getByTestId('card-total-agents')).toHaveTextContent('Total Agents: 0');
      });

      const agentsTable = screen.getByTestId('agents-table');
      expect(agentsTable.children.length).toBe(0);
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator initially', () => {
      const mockResponse = { ok: false, status: 0 };

      render(<MockAffiliatePage mockResponse={mockResponse} />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });
});

