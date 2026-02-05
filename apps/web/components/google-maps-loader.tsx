"use client"

import { useEffect, useState, createContext, useContext, type ReactNode } from "react"
import Script from "next/script"

interface GoogleMapsContextValue {
  isLoaded: boolean
  error: string | null
}

const GoogleMapsContext = createContext<GoogleMapsContextValue>({
  isLoaded: false,
  error: null,
})

/**
 * Hook to check if Google Maps is loaded
 */
export function useGoogleMapsLoaded() {
  return useContext(GoogleMapsContext)
}

/**
 * Provider component that lazily loads Google Maps API
 * Only wrap components/pages that actually need Google Maps
 */
export function GoogleMapsProvider({ children }: { children: ReactNode }) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Check if already loaded (e.g., by another instance)
  useEffect(() => {
    if (typeof window !== "undefined" && window.google?.maps?.places) {
      setIsLoaded(true)
    }
  }, [])

  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY

  if (!apiKey) {
    return (
      <GoogleMapsContext.Provider value={{ isLoaded: false, error: "Google Maps API key not configured" }}>
        {children}
      </GoogleMapsContext.Provider>
    )
  }

  return (
    <GoogleMapsContext.Provider value={{ isLoaded, error }}>
      {!isLoaded && (
        <Script
          src={`https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&loading=async`}
          strategy="lazyOnload"
          onLoad={() => setIsLoaded(true)}
          onError={() => setError("Failed to load Google Maps")}
        />
      )}
      {children}
    </GoogleMapsContext.Provider>
  )
}
