'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, CreditCard, ExternalLink } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface StripeBillingActionsProps {
  accountType: string;
  planSlug: string;
  isSponsored: boolean;
}

export function StripeBillingActions({
  accountType,
  planSlug,
  isSponsored,
}: StripeBillingActionsProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleUpgrade = async (targetPlan: 'pro' | 'team') => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/proxy/v1/billing/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ plan_slug: targetPlan }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || error.detail?.message || 'Failed to create checkout');
      }

      const data = await response.json();
      
      // Redirect to Stripe Checkout
      window.location.href = data.url;
    } catch (error: any) {
      setIsLoading(false);
      toast({
        title: 'Error',
        description: error.message || 'Failed to start checkout',
        variant: 'destructive',
      });
    }
  };

  const handleManageBilling = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/proxy/v1/billing/portal', {
        method: 'GET',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || error.detail?.message || 'Failed to access billing portal');
      }

      const data = await response.json();
      
      // Redirect to Stripe Customer Portal
      window.location.href = data.url;
    } catch (error: any) {
      setIsLoading(false);
      toast({
        title: 'Error',
        description: error.message || 'Failed to access billing portal',
        variant: 'destructive',
      });
    }
  };

  // Sponsored accounts cannot self-upgrade
  if (isSponsored) {
    return (
      <div className="p-4 rounded-lg bg-muted/50 border border-border">
        <p className="text-sm text-muted-foreground">
          Your access is sponsored by your industry affiliate. Contact them for plan changes.
        </p>
      </div>
    );
  }

  // INDUSTRY_AFFILIATE accounts - treat like REGULAR (per spec choice)
  // For now, we'll show the same upgrade options

  // Show upgrade button for free plan
  if (planSlug === 'free') {
    return (
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          onClick={() => handleUpgrade('pro')}
          disabled={isLoading}
          className="flex-1"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </>
          ) : (
            <>
              <CreditCard className="mr-2 h-4 w-4" />
              Upgrade to Pro
            </>
          )}
        </Button>
        <Button
          onClick={() => handleUpgrade('team')}
          disabled={isLoading}
          variant="outline"
          className="flex-1"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading...
            </>
          ) : (
            <>
              <CreditCard className="mr-2 h-4 w-4" />
              Upgrade to Team
            </>
          )}
        </Button>
      </div>
    );
  }

  // Show manage billing for paid plans
  if (planSlug === 'pro' || planSlug === 'team') {
    return (
      <Button
        onClick={handleManageBilling}
        disabled={isLoading}
        variant="outline"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading...
          </>
        ) : (
          <>
            <ExternalLink className="mr-2 h-4 w-4" />
            Manage Billing
          </>
        )}
      </Button>
    );
  }

  // No billing actions for other plans (affiliate, etc.)
  return null;
}



