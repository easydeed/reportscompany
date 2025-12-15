"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Copy, Eye, EyeOff, Trash2 } from "lucide-react"
import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"

const apiKeys = [
  {
    id: "key_001",
    name: "Production API Key",
    key: "sk_live_abc123...",
    created: "2024-01-10",
    lastUsed: "2 hours ago",
  },
  { id: "key_002", name: "Development Key", key: "sk_test_xyz789...", created: "2024-01-05", lastUsed: "1 day ago" },
]

export default function APIKeysPage() {
  const [showKey, setShowKey] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const { toast } = useToast()

  const copyToClipboard = (key: string) => {
    navigator.clipboard.writeText(key)
    toast({
      title: "Copied to clipboard",
      description: "API key has been copied to your clipboard",
    })
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2 text-balance">API Keys</h1>
          <p className="text-muted-foreground text-pretty">Manage your API keys for programmatic access</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-gradient-to-r from-primary to-primary/80 hover:opacity-90">
              <Plus className="w-4 h-4" />
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-display">Create New API Key</DialogTitle>
              <DialogDescription>Give your API key a descriptive name</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="key-name">Key Name</Label>
                <Input id="key-name" placeholder="e.g., Production API Key" />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => setOpen(false)}>Create Key</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="border-border/50 bg-card hover:shadow-lg transition-shadow">
        <CardHeader>
          <CardTitle className="font-display">Your API Keys</CardTitle>
          <CardDescription>Keep your API keys secure and never share them publicly</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {apiKeys.map((apiKey) => (
              <div
                key={apiKey.id}
                className="rounded-xl border border-border/50 p-4 bg-muted/30 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold text-sm mb-1">{apiKey.name}</p>
                    <p className="text-xs text-muted-foreground">
                      Created {apiKey.created} • Last used {apiKey.lastUsed}
                    </p>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Input
                    value={showKey === apiKey.id ? apiKey.key : "••••••••••••••••••••"}
                    readOnly
                    className="font-mono text-xs"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setShowKey(showKey === apiKey.id ? null : apiKey.id)}
                  >
                    {showKey === apiKey.id ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                  <Button variant="outline" size="icon" onClick={() => copyToClipboard(apiKey.key)}>
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="font-display">API Documentation</CardTitle>
          <CardDescription>Learn how to integrate with our API</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Visit our comprehensive API documentation to learn how to generate reports programmatically, manage
            webhooks, and integrate with your applications.
          </p>
          <Button variant="outline">View Documentation</Button>
        </CardContent>
      </Card>
    </div>
  )
}
