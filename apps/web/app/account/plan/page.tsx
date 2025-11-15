'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { PlanPageShell, type PlanPageShellProps } from '@/components/v0-styling/PlanPageShell';

interface PlanUsageData {
  account: {
    id: string;
    name: string;
    account_type: string;
    plan_slug: string;
    monthly_report_limit_override: number | null;
    sponsor_account_id: string | null;
  };
  plan: {
    plan_slug: string;
    plan_name: string;
    monthly_report_limit: number;
    allow_overage: boolean;
    overage_price_cents: number | null;
  };
  usage: {
    report_count: number;
    period_start: string;
    period_end: string;
  };
  decision: 'ALLOW' | 'ALLOW_WITH_WARNING' | 'BLOCK';
  info: {
    ratio: number;
    message: string;
    can_proceed: boolean;
  };
}

export default function PlanPage() {
  const [data, setData] = useState<PlanUsageData | { error: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPlanUsage() {
      try {
        const response = await fetch('/api/proxy/v1/account/plan-usage', {
          credentials: 'include',
          cache: 'no-store',
        });

        if (!response.ok) {
          setData({ error: 'Failed to load plan information' });
          return;
        }

        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch plan usage:', error);
        setData({ error: 'Failed to load plan information' });
      } finally {
        setLoading(false);
      }
    }

    fetchPlanUsage();
  }, []);

  // Handle loading
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Plan & Usage</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Loading...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Handle errors
  if (!data || 'error' in data) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight">Plan & Usage</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">{data?.error || 'Failed to load'}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Map fetched data to shell props
  const shellProps: PlanPageShellProps = {
    account: data.account,
    plan: data.plan,
    usage: data.usage,
    decision: data.decision,
    info: data.info,
  };

  return <PlanPageShell {...shellProps} />;
}

