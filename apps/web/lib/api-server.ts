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

/** Maximum time to wait for an API response before aborting */
const API_TIMEOUT_MS = 10000 // 10 seconds - fail fast rather than hang

export type ApiResponse<T> = {
  data: T | null
  error: string | null
  status: number
}

export type CacheOptions = {
  /** Seconds to cache the response. 0 = no cache (default) */
  revalidate?: number
  /** Tags for on-demand revalidation */
  tags?: string[]
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
    options?: { body?: any; params?: Record<string, string>; cache?: CacheOptions }
  ): Promise<ApiResponse<T>> {
    if (!token) {
      return { data: null, error: 'Unauthorized', status: 401 }
    }

    // Create abort controller for timeout protection
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS)

    try {
      let url = `${API_BASE}${path}`
      
      // Add query params if provided
      if (options?.params) {
        const searchParams = new URLSearchParams(options.params)
        url += `?${searchParams.toString()}`
      }

      // Build fetch options with caching support
      const fetchOptions: RequestInit & { next?: { revalidate?: number; tags?: string[] } } = {
        method,
        headers: {
          'Cookie': `mr_token=${token}`,
          ...(options?.body && { 'Content-Type': 'application/json' }),
        },
        body: options?.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal, // Enable timeout abort
      }

      // Apply caching options (Next.js specific)
      if (options?.cache?.revalidate !== undefined || options?.cache?.tags) {
        fetchOptions.next = {
          revalidate: options.cache.revalidate ?? 0,
          tags: options.cache.tags ?? [],
        }
      } else {
        // Default: no caching for mutations, no-store for GETs without explicit cache
        fetchOptions.cache = 'no-store'
      }

      const response = await fetch(url, fetchOptions)

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
      // Handle timeout abort specifically
      if (error instanceof DOMException && error.name === 'AbortError') {
        console.error(`[API] ${method} ${path} timed out after ${API_TIMEOUT_MS}ms`)
        return {
          data: null,
          error: `Request timed out (${API_TIMEOUT_MS / 1000}s)`,
          status: 408
        }
      }
      console.error(`[API] ${method} ${path} error:`, error)
      return { 
        data: null, 
        error: error instanceof Error ? error.message : 'Network error',
        status: 500 
      }
    } finally {
      clearTimeout(timeoutId)
    }
  }

  return {
    /** Check if user is authenticated */
    isAuthenticated: () => !!token,
    
    /** Get the raw token (for edge cases) */
    getToken: () => token,

    /** GET request with optional caching */
    get: <T>(path: string, options?: { params?: Record<string, string>; cache?: CacheOptions }) => 
      request<T>('GET', path, options),

    /** POST request (no caching) */
    post: <T>(path: string, body?: any) => 
      request<T>('POST', path, { body }),

    /** PATCH request (no caching) */
    patch: <T>(path: string, body?: any) => 
      request<T>('PATCH', path, { body }),

    /** DELETE request (no caching) */
    delete: <T>(path: string) => 
      request<T>('DELETE', path),
  }
}

/**
 * Simple fetch helper that returns data or null (for backwards compatibility)
 * Use this for quick migrations from the old fetchWithAuth pattern.
 */
export async function fetchApi<T>(path: string, cache?: CacheOptions): Promise<T | null> {
  const api = await createServerApi()
  const { data } = await api.get<T>(path, { cache })
  return data
}

/**
 * Fetch multiple endpoints in parallel with optional caching
 */
export async function fetchApiParallel<T extends any[]>(
  requests: (string | { path: string; cache?: CacheOptions })[]
): Promise<{ [K in keyof T]: T[K] | null }> {
  const api = await createServerApi()
  const results = await Promise.all(
    requests.map(req => {
      if (typeof req === 'string') {
        return api.get(req)
      }
      return api.get(req.path, { cache: req.cache })
    })
  )
  return results.map(r => r.data) as { [K in keyof T]: T[K] | null }
}

/**
 * Pre-configured cache durations for common endpoints
 */
export const CACHE_DURATIONS = {
  /** User profile - changes rarely, 5 min cache */
  USER_PROFILE: { revalidate: 300, tags: ['user-profile'] } as CacheOptions,
  /** Account info - changes rarely, 5 min cache */
  ACCOUNT: { revalidate: 300, tags: ['account'] } as CacheOptions,
  /** Plan/usage - changes on report generation, 2 min cache */
  PLAN_USAGE: { revalidate: 120, tags: ['plan-usage', 'usage'] } as CacheOptions,
  /** Contacts list - changes on add/remove, 1 min cache */
  CONTACTS: { revalidate: 60, tags: ['contacts'] } as CacheOptions,
}
