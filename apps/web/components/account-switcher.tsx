'use client';

import { useEffect, useState } from 'react';
import { ChevronDown, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';

interface Account {
  account_id: string;
  name: string;
  account_type: 'REGULAR' | 'INDUSTRY_AFFILIATE';
  plan_slug: string;
  role: string;
  created_at?: string;
}

interface AccountsResponse {
  accounts: Account[];
  count: number;
}

export function AccountSwitcher() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [currentAccount, setCurrentAccount] = useState<Account | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchAccounts();
  }, []);

  async function fetchAccounts() {
    try {
      const response = await fetch('/api/proxy/v1/account/accounts');
      
      if (!response.ok) {
        throw new Error('Failed to fetch accounts');
      }

      const data: AccountsResponse = await response.json();
      setAccounts(data.accounts);
      
      // Set the first account as current (backend determines which one is active)
      if (data.accounts.length > 0) {
        setCurrentAccount(data.accounts[0]);
      }
    } catch (error) {
      console.error('Failed to load accounts:', error);
      toast({
        title: 'Error',
        description: 'Failed to load account information',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function switchAccount(accountId: string) {
    if (isSwitching) return;
    
    setIsSwitching(true);

    try {
      const response = await fetch('/api/proxy/v1/account/use', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ account_id: accountId }),
      });

      if (!response.ok) {
        throw new Error('Failed to switch account');
      }

      toast({
        title: 'Account switched',
        description: 'Reloading application...',
      });

      // Hard refresh to update all data with new account context
      setTimeout(() => {
        window.location.href = '/app';
      }, 500);
    } catch (error) {
      console.error('Failed to switch account:', error);
      toast({
        title: 'Error',
        description: 'Failed to switch account. Please try again.',
        variant: 'destructive',
      });
      setIsSwitching(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
        <Building2 className="h-4 w-4" />
        <span>Loading...</span>
      </div>
    );
  }

  if (!currentAccount) {
    return null;
  }

  // Single account - just show the name (no dropdown)
  if (accounts.length <= 1) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 text-sm">
        <Building2 className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">{currentAccount.name}</span>
      </div>
    );
  }

  // Multiple accounts - show dropdown
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="flex items-center gap-2 min-w-[200px] justify-between"
          disabled={isSwitching}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <span className="font-medium truncate">{currentAccount.name}</span>
          </div>
          <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[250px]">
        <DropdownMenuLabel>Switch Account</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {accounts.map((account) => (
          <DropdownMenuItem
            key={account.account_id}
            onClick={() => switchAccount(account.account_id)}
            disabled={isSwitching || account.account_id === currentAccount.account_id}
            className="flex flex-col items-start gap-1 cursor-pointer"
          >
            <div className="flex items-center gap-2 w-full">
              <span className="font-medium">{account.name}</span>
              {account.account_id === currentAccount.account_id && (
                <span className="ml-auto text-xs text-primary">Current</span>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="capitalize">{account.account_type.replace('_', ' ').toLowerCase()}</span>
              <span>•</span>
              <span>{account.plan_slug}</span>
              <span>•</span>
              <span className="capitalize">{account.role}</span>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

