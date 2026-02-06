'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Show cached data immediately, refetch in background after 2 min
            staleTime: 2 * 60 * 1000,
            // Keep unused cache for 10 minutes
            gcTime: 10 * 60 * 1000,
            // Refresh when user tabs back
            refetchOnWindowFocus: true,
            // Refresh on network recovery
            refetchOnReconnect: true,
            // Retry failed requests twice
            retry: 2,
            retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 5000),
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
