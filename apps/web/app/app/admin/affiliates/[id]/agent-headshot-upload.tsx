"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ImageUpload } from "@/components/ui/image-upload"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Camera, Loader2 } from "lucide-react"

interface AgentHeadshotUploadProps {
  accountId: string
  agentName: string
  currentHeadshot?: string | null
}

export function AgentHeadshotUpload({ accountId, agentName, currentHeadshot }: AgentHeadshotUploadProps) {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [headshotUrl, setHeadshotUrl] = useState<string | null>(currentHeadshot || null)
  const [error, setError] = useState<string | null>(null)

  async function handleSave() {
    if (!headshotUrl) return

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`/api/proxy/v1/admin/agents/${accountId}/headshot`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ headshot_url: headshotUrl }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || data.error || "Failed to update headshot")
      }

      setOpen(false)
      router.refresh()
    } catch (err: any) {
      setError(err.message || "Failed to update headshot")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8" title="Upload headshot">
          <Camera className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Headshot</DialogTitle>
          <DialogDescription>
            Upload a professional headshot for {agentName}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <ImageUpload
            label="Agent Headshot"
            value={headshotUrl}
            onChange={setHeadshotUrl}
            assetType="headshot"
            aspectRatio="square"
            helpText="Square image recommended (at least 200x200px)"
          />

          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={loading || !headshotUrl}>
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Save
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
