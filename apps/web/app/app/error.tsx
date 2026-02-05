"use client"

import { Button } from "@/components/ui/button"
import { AlertCircle, RefreshCw, Home } from "lucide-react"
import Link from "next/link"
import { useEffect } from "react"

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to console for debugging
    console.error("App error boundary caught:", error)
  }, [error])

  const isTimeout = error.message?.includes('timeout') || error.message?.includes('timed out')
  const isNetworkError = error.message?.includes('Network') || error.message?.includes('fetch')

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4 px-4">
      <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center">
        <AlertCircle className="w-8 h-8 text-destructive" />
      </div>
      
      <div className="text-center space-y-2">
        <h2 className="text-xl font-semibold text-foreground">Something went wrong</h2>
        <p className="text-sm text-muted-foreground max-w-md">
          {isTimeout 
            ? "The server is taking too long to respond. This is usually temporary."
            : isNetworkError
            ? "We're having trouble connecting to our servers. Please check your connection."
            : "We encountered an unexpected error. This is usually temporary."
          }
        </p>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <Button onClick={reset} variant="default">
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
        <Button asChild variant="outline">
          <Link href="/app">
            <Home className="w-4 h-4 mr-2" />
            Dashboard
          </Link>
        </Button>
      </div>

      {process.env.NODE_ENV === 'development' && error.digest && (
        <p className="text-xs text-muted-foreground font-mono mt-4">
          Error ID: {error.digest}
        </p>
      )}
    </div>
  )
}
