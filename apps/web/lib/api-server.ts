/**
 * Server-side API utilities for Next.js Server Components
 * 
 * This module provides a standardized way to make authenticated API calls
 * from server components to the backend API.
 * 
 * Usage:
 *   import { createServerApi } from '@/lib/api-server'
 *   
 *   const api = await createServerApi()
 *   const data = await api.get('/v1/me')
 */

import { cookies } from 'next/headers'

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || 'https://reportscompany.onrender.com').replace(/\/$/, '')

export type ApiResponse<T> = {
  data: T | null
  error: string | null
  status: number
}

/**
 * Creates an authenticated API client for server components.
 * Automatically reads the auth token from cookies.
 * 
 * @returns API client with get, post, patch, delete methods
 * @throws Redirects to /login if no token present (optional)
 */
export async function createServerApi() {
  const cookieStore = await cookies()
  const token = cookieStore.get('mr_token')?.value

  async function request<T>(
    method: string,
    path: string,
    options?: { body?: any; params?: Record<string, string> }
  ): Promise<ApiResponse<T>> {
    if (!token) {
      return { data: null, error: 'Unauthorized', status: 401 }
    }

    try {
      let url = `${API_BASE}${path}`
      
      // Add query params if provided
      if (options?.params) {
        const searchParams = new URLSearchParams(options.params)
        url += `?${searchParams.toString()}`
      }

      const response = await fetch(url, {
        method,
        headers: {
          'Cookie': `mr_token=${token}`,
          ...(options?.body && { 'Content-Type': 'application/json' }),
        },
        body: options?.body ? JSON.stringify(options.body) : undefined,
        cache: 'no-store',
      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        console.error(`[API] ${method} ${path} failed:`, response.status, data)
        return { 
          data: null, 
          error: data?.detail || data?.error || `Request failed with status ${response.status}`,
          status: response.status 
        }
      }

      return { data, error: null, status: response.status }
    } catch (error) {
      console.error(`[API] ${method} ${path} error:`, error)
      return { 
        data: null, 
        error: error instanceof Error ? error.message : 'Network error',
        status: 500 
      }
    }
  }

  return {
    /** Check if user is authenticated */
    isAuthenticated: () => !!token,
    
    /** Get the raw token (for edge cases) */
    getToken: () => token,

    /** GET request */
    get: <T>(path: string, params?: Record<string, string>) => 
      request<T>('GET', path, { params }),

    /** POST request */
    post: <T>(path: string, body?: any) => 
      request<T>('POST', path, { body }),

    /** PATCH request */
    patch: <T>(path: string, body?: any) => 
      request<T>('PATCH', path, { body }),

    /** DELETE request */
    delete: <T>(path: string) => 
      request<T>('DELETE', path),
  }
}

/**
 * Simple fetch helper that returns data or null (for backwards compatibility)
 * Use this for quick migrations from the old fetchWithAuth pattern.
 */
export async function fetchApi<T>(path: string): Promise<T | null> {
  const api = await createServerApi()
  const { data } = await api.get<T>(path)
  return data
}

/**
 * Fetch multiple endpoints in parallel
 */
export async function fetchApiParallel<T extends any[]>(
  paths: string[]
): Promise<{ [K in keyof T]: T[K] | null }> {
  const api = await createServerApi()
  const results = await Promise.all(
    paths.map(path => api.get(path))
  )
  return results.map(r => r.data) as { [K in keyof T]: T[K] | null }
}

