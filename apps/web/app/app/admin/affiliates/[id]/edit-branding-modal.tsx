'use client'

import { useState } from "react"
import { Paintbrush, Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/use-toast"

interface Branding {
  brand_display_name: string | null
  logo_url: string | null
  primary_color: string | null
  accent_color: string | null
  rep_photo_url: string | null
  contact_line1: string | null
  contact_line2: string | null
  website_url: string | null
}

interface EditBrandingModalProps {
  affiliateId: string
  branding: Branding
  onSaved: (branding: Branding) => void
}

export function EditBrandingModal({ affiliateId, branding, onSaved }: EditBrandingModalProps) {
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  const [form, setForm] = useState({
    brand_display_name: branding.brand_display_name || "",
    logo_url: branding.logo_url || "",
    primary_color: branding.primary_color || "#7C3AED",
    accent_color: branding.accent_color || "#F26B2B",
    website_url: branding.website_url || "",
    contact_line1: branding.contact_line1 || "",
    contact_line2: branding.contact_line2 || "",
    rep_photo_url: branding.rep_photo_url || "",
  })

  function handleOpen(isOpen: boolean) {
    if (isOpen) {
      setForm({
        brand_display_name: branding.brand_display_name || "",
        logo_url: branding.logo_url || "",
        primary_color: branding.primary_color || "#7C3AED",
        accent_color: branding.accent_color || "#F26B2B",
        website_url: branding.website_url || "",
        contact_line1: branding.contact_line1 || "",
        contact_line2: branding.contact_line2 || "",
        rep_photo_url: branding.rep_photo_url || "",
      })
    }
    setOpen(isOpen)
  }

  function setField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave() {
    setSaving(true)
    try {
      const res = await fetch(
        `/api/proxy/v1/admin/affiliates/${affiliateId}/branding`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            brand_display_name: form.brand_display_name || undefined,
            logo_url: form.logo_url || undefined,
            primary_color: form.primary_color || undefined,
            accent_color: form.accent_color || undefined,
            website_url: form.website_url || undefined,
            contact_line1: form.contact_line1 || undefined,
            contact_line2: form.contact_line2 || undefined,
            rep_photo_url: form.rep_photo_url || undefined,
          }),
        }
      )

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || data.error || "Failed to save branding")
      }

      const data = await res.json()
      onSaved(data.branding)
      setOpen(false)
      toast({ title: "Branding updated", description: "Affiliate branding has been saved." })
    } catch (err) {
      console.error("Save branding failed:", err)
      toast({
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to save branding",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Paintbrush className="h-4 w-4 mr-2" />
          Edit Branding
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Edit Affiliate Branding</DialogTitle>
          <DialogDescription>
            Update the white-label branding for this affiliate and all their sponsored agents.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto pr-1">
          <div className="space-y-1.5">
            <Label htmlFor="brand_display_name">Display Name</Label>
            <Input
              id="brand_display_name"
              value={form.brand_display_name}
              onChange={(e) => setField("brand_display_name", e.target.value)}
              placeholder="Acme Title Company"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="logo_url">Logo URL</Label>
            <Input
              id="logo_url"
              value={form.logo_url}
              onChange={(e) => setField("logo_url", e.target.value)}
              placeholder="https://..."
            />
            {form.logo_url && (
              <img
                src={form.logo_url}
                alt="Logo preview"
                className="h-10 mt-1 rounded object-contain bg-muted p-1"
              />
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="primary_color">Primary Color</Label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  id="primary_color"
                  value={form.primary_color}
                  onChange={(e) => setField("primary_color", e.target.value)}
                  className="h-9 w-12 rounded border cursor-pointer"
                />
                <Input
                  value={form.primary_color}
                  onChange={(e) => setField("primary_color", e.target.value)}
                  className="font-mono text-sm"
                  maxLength={7}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="accent_color">Accent Color</Label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  id="accent_color"
                  value={form.accent_color}
                  onChange={(e) => setField("accent_color", e.target.value)}
                  className="h-9 w-12 rounded border cursor-pointer"
                />
                <Input
                  value={form.accent_color}
                  onChange={(e) => setField("accent_color", e.target.value)}
                  className="font-mono text-sm"
                  maxLength={7}
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="website_url">Website</Label>
            <Input
              id="website_url"
              value={form.website_url}
              onChange={(e) => setField("website_url", e.target.value)}
              placeholder="https://acmetitle.com"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="contact_line1">Contact Line 1</Label>
              <Input
                id="contact_line1"
                value={form.contact_line1}
                onChange={(e) => setField("contact_line1", e.target.value)}
                placeholder="(555) 123-4567"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contact_line2">Contact Line 2</Label>
              <Input
                id="contact_line2"
                value={form.contact_line2}
                onChange={(e) => setField("contact_line2", e.target.value)}
                placeholder="info@acmetitle.com"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="rep_photo_url">Rep Photo URL</Label>
            <Input
              id="rep_photo_url"
              value={form.rep_photo_url}
              onChange={(e) => setField("rep_photo_url", e.target.value)}
              placeholder="https://..."
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              "Save Branding"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
