"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Trash2, CheckCircle2, XCircle } from "lucide-react"
import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const webhooks = [
  {
    id: "wh_001",
    url: "https://api.example.com/webhooks/reports",
    events: ["report.created", "report.completed"],
    status: "active",
    lastTriggered: "2 hours ago",
  },
  {
    id: "wh_002",
    url: "https://app.example.com/api/notifications",
    events: ["report.failed"],
    status: "inactive",
    lastTriggered: "Never",
  },
]

export default function WebhooksPage() {
  const [open, setOpen] = useState(false)

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-3xl mb-2">Webhooks</h1>
          <p className="text-muted-foreground">Receive real-time notifications about report events</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              Create Webhook
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-display">Create New Webhook</DialogTitle>
              <DialogDescription>Configure a webhook endpoint to receive event notifications</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="webhook-url">Webhook URL</Label>
                <Input id="webhook-url" type="url" placeholder="https://api.example.com/webhooks" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="events">Events</Label>
                <Select>
                  <SelectTrigger id="events">
                    <SelectValue placeholder="Select events to listen to" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Events</SelectItem>
                    <SelectItem value="created">Report Created</SelectItem>
                    <SelectItem value="completed">Report Completed</SelectItem>
                    <SelectItem value="failed">Report Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => setOpen(false)}>Create Webhook</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Your Webhooks</CardTitle>
          <CardDescription>Manage webhook endpoints for event notifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {webhooks.map((webhook) => (
              <div key={webhook.id} className="glass rounded-lg border border-border p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-sm font-mono">{webhook.url}</p>
                      {webhook.status === "active" ? (
                        <CheckCircle2 className="w-4 h-4 text-primary" />
                      ) : (
                        <XCircle className="w-4 h-4 text-muted-foreground" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">Last triggered: {webhook.lastTriggered}</p>
                    <div className="flex gap-1">
                      {webhook.events.map((event) => (
                        <span key={event} className="text-xs px-2 py-1 rounded-full bg-muted font-mono">
                          {event}
                        </span>
                      ))}
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="font-display">Webhook Events</CardTitle>
          <CardDescription>Available events you can subscribe to</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { event: "report.created", description: "Triggered when a new report is created" },
              { event: "report.completed", description: "Triggered when a report generation is completed" },
              { event: "report.failed", description: "Triggered when a report generation fails" },
              { event: "report.viewed", description: "Triggered when a report is viewed" },
            ].map((item) => (
              <div key={item.event} className="flex items-start gap-3 py-2">
                <code className="text-xs font-mono bg-muted px-2 py-1 rounded">{item.event}</code>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
