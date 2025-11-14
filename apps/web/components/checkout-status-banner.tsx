'use client';

import { useSearchParams } from 'next/navigation';
import { CheckCircle2, XCircle, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

export function CheckoutStatusBanner() {
  const searchParams = useSearchParams();
  const checkoutStatus = searchParams?.get('checkout');
  const [dismissed, setDismissed] = useState(false);

  if (!checkoutStatus || dismissed) {
    return null;
  }

  if (checkoutStatus === 'success') {
    return (
      <Alert className="border-green-500/20 bg-green-500/10 relative">
        <CheckCircle2 className="h-4 w-4 text-green-500" />
        <AlertTitle className="text-green-700 dark:text-green-400">
          Payment Successful!
        </AlertTitle>
        <AlertDescription className="text-green-700/90 dark:text-green-400/90">
          Your subscription is being activated. Your plan will update shortly and limits will be adjusted.
        </AlertDescription>
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2 h-6 w-6 p-0"
          onClick={() => setDismissed(true)}
        >
          <X className="h-4 w-4" />
        </Button>
      </Alert>
    );
  }

  if (checkoutStatus === 'cancel') {
    return (
      <Alert className="border-yellow-500/20 bg-yellow-500/10 relative">
        <XCircle className="h-4 w-4 text-yellow-500" />
        <AlertTitle className="text-yellow-700 dark:text-yellow-400">
          Payment Cancelled
        </AlertTitle>
        <AlertDescription className="text-yellow-700/90 dark:text-yellow-400/90">
          Your payment was cancelled. You can try again anytime using the upgrade button below.
        </AlertDescription>
        <Button
          variant="ghost"
          size="sm"
          className="absolute top-2 right-2 h-6 w-6 p-0"
          onClick={() => setDismissed(true)}
        >
          <X className="h-4 w-4" />
        </Button>
      </Alert>
    );
  }

  return null;
}



