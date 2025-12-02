"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, CheckCircle, Copy } from "lucide-react"

interface InviteAgentFormProps {
  affiliateId: string
  affiliateName: string
}

export function InviteAgentForm({ affiliateId, affiliateName }: InviteAgentFormProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<{ email: string; inviteUrl: string } | null>(null)
  const [copied, setCopied] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    const formData = new FormData(e.currentTarget)
    const agentName = formData.get("agent_name") as string
    const agentEmail = formData.get("agent_email") as string

    try {
      const res = await fetch(`/api/proxy/v1/admin/affiliates/${affiliateId}/invite-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          affiliate_id: affiliateId,
          agent_name: agentName,
          agent_email: agentEmail,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || "Failed to invite agent")
      }

      setSuccess({
        email: agentEmail,
        inviteUrl: data.invite_url,
      })

      // Reset form
      e.currentTarget.reset()

      // Refresh the page to show new agent
      router.refresh()
    } catch (err: any) {
      setError(err.message || "Failed to invite agent")
    } finally {
      setLoading(false)
    }
  }

  function copyToClipboard() {
    if (success?.inviteUrl) {
      navigator.clipboard.writeText(success.inviteUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[200px]">
          <Label htmlFor="agent_name">Agent/Company Name</Label>
          <Input
            id="agent_name"
            name="agent_name"
            placeholder="John Smith Realty"
            required
            disabled={loading}
          />
        </div>
        <div className="flex-1 min-w-[200px]">
          <Label htmlFor="agent_email">Email Address</Label>
          <Input
            id="agent_email"
            name="agent_email"
            type="email"
            placeholder="agent@example.com"
            required
            disabled={loading}
          />
        </div>
        <Button type="submit" disabled={loading}>
          {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Send Invite
        </Button>
      </form>

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mt-4 border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <div className="font-medium">Invitation sent to {success.email}</div>
            <div className="text-sm mt-1">
              The agent will receive an email with instructions to set up their account.
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Input
                value={success.inviteUrl}
                readOnly
                className="text-xs bg-white"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={copyToClipboard}
                className="shrink-0"
              >
                {copied ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
