'use client'

import { useQuery } from '@tanstack/react-query'

export type User = {
  id: string
  email: string
  first_name?: string
  last_name?: string
  avatar_url?: string
  role: 'USER' | 'ADMIN'
  account_type: 'REGULAR' | 'INDUSTRY_AFFILIATE'
  account_id: string
  job_title?: string
  company_name?: string
  phone?: string
  website?: string
  email_verified?: boolean
}

async function fetchUser(): Promise<User> {
  const res = await fetch('/api/proxy/v1/users/me', {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json()
}

export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: fetchUser,
    staleTime: 10 * 60 * 1000, // User data rarely changes — cache 10 min
  })
}
