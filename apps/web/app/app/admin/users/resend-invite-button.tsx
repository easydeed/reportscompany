"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, Mail, CheckCircle } from "lucide-react"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface ResendInviteButtonProps {
  userId: string
  email: string
}

export function ResendInviteButton({ userId, email }: ResendInviteButtonProps) {
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleResend() {
    setLoading(true)
    try {
      const res = await fetch(`/api/proxy/v1/admin/users/${userId}/resend-invite`, {
        method: "POST",
      })

      if (res.ok) {
        setSent(true)
        setTimeout(() => setSent(false), 3000)
      }
    } catch (error) {
      console.error("Failed to resend invite:", error)
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <Button variant="ghost" size="sm" disabled className="text-green-600">
        <CheckCircle className="h-4 w-4 mr-1" />
        Sent
      </Button>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResend}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Mail className="h-4 w-4" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Resend invite to {email}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
