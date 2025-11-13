"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ColorPicker } from "@/components/color-picker"
import { FileUploader } from "@/components/file-uploader"
import { useState } from "react"
import { Save } from "lucide-react"

export default function BrandingPage() {
  const [primaryColor, setPrimaryColor] = useState("#2563EB")
  const [accentColor, setAccentColor] = useState("#F26B2B")

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="font-display font-bold text-3xl mb-2">Branding</h1>
        <p className="text-muted-foreground">Customize your report appearance with your brand identity</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-display">Logo</CardTitle>
              <CardDescription>Upload your company logo for reports</CardDescription>
            </CardHeader>
            <CardContent>
              <FileUploader accept="image/*" maxSize={5} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Colors</CardTitle>
              <CardDescription>Choose your brand colors</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Primary Color</Label>
                <ColorPicker value={primaryColor} onChange={setPrimaryColor} />
              </div>
              <div className="space-y-2">
                <Label>Accent Color</Label>
                <ColorPicker value={accentColor} onChange={setAccentColor} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-display">Contact Information</CardTitle>
              <CardDescription>Displayed on all reports</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="company">Company Name</Label>
                <Input id="company" placeholder="Acme Realty" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" type="tel" placeholder="(555) 123-4567" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="contact@acmerealty.com" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="website">Website</Label>
                <Input id="website" type="url" placeholder="https://acmerealty.com" />
              </div>
            </CardContent>
          </Card>

          <Button className="w-full gap-2">
            <Save className="w-4 h-4" />
            Save Branding
          </Button>
        </div>

        <div>
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="font-display">Preview</CardTitle>
              <CardDescription>See how your branding looks on reports</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="aspect-[8.5/11] bg-muted rounded-lg border border-border p-6 space-y-4">
                <div className="flex items-center justify-between pb-4 border-b border-border">
                  <div className="w-16 h-16 rounded bg-primary/10 flex items-center justify-center">
                    <span className="text-xs font-semibold" style={{ color: primaryColor }}>
                      LOGO
                    </span>
                  </div>
                  <div className="text-right text-xs">
                    <p className="font-semibold">Acme Realty</p>
                    <p className="text-muted-foreground">(555) 123-4567</p>
                  </div>
                </div>
                <div>
                  <h3 className="font-display font-bold text-lg mb-2" style={{ color: primaryColor }}>
                    Market Analysis Report
                  </h3>
                  <p className="text-xs text-muted-foreground">San Francisco, CA • Q4 2024</p>
                </div>
                <div className="space-y-2">
                  <div className="h-2 bg-background rounded" />
                  <div className="h-2 bg-background rounded w-4/5" />
                  <div className="h-2 bg-background rounded w-3/5" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="h-20 rounded" style={{ backgroundColor: primaryColor + "20" }} />
                  <div className="h-20 rounded" style={{ backgroundColor: accentColor + "20" }} />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
