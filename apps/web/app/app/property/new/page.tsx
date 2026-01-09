"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Search,
  Home,
  Palette,
  CheckCircle2,
  Loader2,
  ArrowLeft,
  ArrowRight,
  FileText,
  XCircle,
} from "lucide-react"
import { apiFetch } from "@/lib/api"

type PropertyData = {
  full_address: string
  street: string
  city: string
  state: string
  zip_code: string
  county: string
  apn: string
  owner_name: string
  legal_description: string
  bedrooms?: number
  bathrooms?: number
  sqft?: number
  lot_size?: number
  year_built?: number
  property_type: string
  assessed_value?: number
}

type Step = "search" | "review" | "confirm"

const THEME_COLORS = [
  { name: "Navy", value: "#0d294b" },
  { name: "Blue", value: "#2563eb" },
  { name: "Emerald", value: "#059669" },
  { name: "Purple", value: "#7c3aed" },
  { name: "Rose", value: "#e11d48" },
  { name: "Orange", value: "#ea580c" },
]

export default function NewPropertyReportPage() {
  const router = useRouter()
  const [step, setStep] = useState<Step>("search")
  
  // Search state
  const [address, setAddress] = useState("")
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [propertyData, setPropertyData] = useState<PropertyData | null>(null)
  
  // Report options
  const [reportType, setReportType] = useState<"seller" | "buyer">("seller")
  const [accentColor, setAccentColor] = useState("#0d294b")
  const [language, setLanguage] = useState<"en" | "es">("en")
  
  // Generation state
  const [generating, setGenerating] = useState(false)
  const [generationError, setGenerationError] = useState<string | null>(null)
  const [generatedReportId, setGeneratedReportId] = useState<string | null>(null)

  async function handleSearch() {
    if (!address.trim()) return
    
    setSearchLoading(true)
    setSearchError(null)
    
    try {
      const data = await apiFetch("/v1/property/search", {
        method: "POST",
        body: JSON.stringify({ address: address.trim() }),
      })
      
      if (data.property) {
        setPropertyData(data.property)
        setStep("review")
      } else {
        setSearchError("Property not found. Please check the address and try again.")
      }
    } catch (e: any) {
      setSearchError(e.message || "Failed to search property")
    } finally {
      setSearchLoading(false)
    }
  }

  async function handleGenerate() {
    if (!propertyData) return
    
    setGenerating(true)
    setGenerationError(null)
    
    try {
      const response = await apiFetch("/v1/property/reports", {
        method: "POST",
        body: JSON.stringify({
          report_type: reportType,
          accent_color: accentColor,
          language,
          property_address: propertyData.street,
          property_city: propertyData.city,
          property_state: propertyData.state,
          property_zip: propertyData.zip_code,
          property_county: propertyData.county,
          apn: propertyData.apn,
          owner_name: propertyData.owner_name,
          legal_description: propertyData.legal_description,
          property_type: propertyData.property_type,
        }),
      })
      
      setGeneratedReportId(response.id)
      setStep("confirm")
      
      // Poll for completion
      pollReportStatus(response.id)
    } catch (e: any) {
      setGenerationError(e.message || "Failed to create report")
      setGenerating(false)
    }
  }

  async function pollReportStatus(reportId: string) {
    let attempts = 0
    const maxAttempts = 60 // 60 seconds timeout
    
    const poll = async () => {
      attempts++
      try {
        const report = await apiFetch(`/v1/property/reports/${reportId}`)
        
        if (report.status === "complete") {
          setGenerating(false)
          return
        }
        
        if (report.status === "failed") {
          setGenerating(false)
          setGenerationError("Report generation failed. Please try again.")
          return
        }
        
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000)
        } else {
          setGenerating(false)
        }
      } catch (e) {
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000)
        }
      }
    }
    
    poll()
  }

  function goBack() {
    if (step === "review") {
      setStep("search")
    } else if (step === "confirm") {
      router.push(`/app/property/${generatedReportId}`)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="font-bold text-2xl">Create Property Report</h1>
          <p className="text-muted-foreground">Generate a professional property report with QR code</p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-2">
        {["search", "review", "confirm"].map((s, i) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                step === s
                  ? "bg-primary text-primary-foreground"
                  : ["review", "confirm"].indexOf(step) >= i
                  ? "bg-green-500 text-white"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {["review", "confirm"].indexOf(step) > i ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                i + 1
              )}
            </div>
            {i < 2 && (
              <div
                className={`w-12 h-1 mx-2 rounded ${
                  ["review", "confirm"].indexOf(step) > i ? "bg-green-500" : "bg-muted"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Search Property */}
      {step === "search" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              Search Property
            </CardTitle>
            <CardDescription>
              Enter the property address to fetch property data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="address">Property Address</Label>
              <div className="flex gap-2">
                <Input
                  id="address"
                  placeholder="e.g., 714 Vine St, Anaheim, CA 92805"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="flex-1"
                />
                <Button onClick={handleSearch} disabled={searchLoading || !address.trim()}>
                  {searchLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>

            {searchError && (
              <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
                {searchError}
              </div>
            )}

            <p className="text-xs text-muted-foreground">
              Enter a full address including city, state, and ZIP code for best results.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Review & Configure */}
      {step === "review" && propertyData && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Home className="w-5 h-5" />
                Property Details
              </CardTitle>
              <CardDescription>
                Review the property information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Address</p>
                  <p className="font-medium">{propertyData.full_address}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">County</p>
                  <p className="font-medium">{propertyData.county || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">APN</p>
                  <p className="font-medium">{propertyData.apn || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Owner</p>
                  <p className="font-medium">{propertyData.owner_name || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Bedrooms / Bathrooms</p>
                  <p className="font-medium">
                    {propertyData.bedrooms || "N/A"} bed / {propertyData.bathrooms || "N/A"} bath
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Square Feet</p>
                  <p className="font-medium">
                    {propertyData.sqft ? propertyData.sqft.toLocaleString() : "N/A"} sqft
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Year Built</p>
                  <p className="font-medium">{propertyData.year_built || "N/A"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Property Type</p>
                  <p className="font-medium">{propertyData.property_type || "N/A"}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Report Options
              </CardTitle>
              <CardDescription>
                Customize your report appearance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Report Type</Label>
                  <Select value={reportType} onValueChange={(v) => setReportType(v as "seller" | "buyer")}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="seller">Seller Report</SelectItem>
                      <SelectItem value="buyer">Buyer Report</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Language</Label>
                  <Select value={language} onValueChange={(v) => setLanguage(v as "en" | "es")}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Accent Color</Label>
                <div className="flex gap-2">
                  {THEME_COLORS.map((color) => (
                    <button
                      key={color.value}
                      onClick={() => setAccentColor(color.value)}
                      className={`w-10 h-10 rounded-lg transition-all ${
                        accentColor === color.value
                          ? "ring-2 ring-offset-2 ring-primary scale-110"
                          : "hover:scale-105"
                      }`}
                      style={{ backgroundColor: color.value }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep("search")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <Button onClick={handleGenerate} disabled={generating} className="flex-1">
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  Generate Report
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </div>

          {generationError && (
            <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
              {generationError}
            </div>
          )}
        </div>
      )}

      {/* Step 3: Confirmation */}
      {step === "confirm" && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center space-y-6">
              {generating ? (
                <>
                  <div className="relative inline-block">
                    <div className="w-20 h-20 rounded-full border-4 border-primary/20 mx-auto" />
                    <div className="absolute inset-0 w-20 h-20 rounded-full border-4 border-transparent border-t-primary animate-spin mx-auto" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <FileText className="w-8 h-8 text-primary animate-pulse" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Generating Your Report</h3>
                    <p className="text-muted-foreground">
                      This usually takes 15-30 seconds...
                    </p>
                  </div>
                </>
              ) : generationError ? (
                <>
                  <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mx-auto">
                    <XCircle className="w-10 h-10 text-red-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Generation Failed</h3>
                    <p className="text-muted-foreground">{generationError}</p>
                  </div>
                  <Button onClick={() => setStep("review")}>Try Again</Button>
                </>
              ) : (
                <>
                  <div className="relative inline-block">
                    <div className="w-20 h-20 rounded-full bg-green-500/10 flex items-center justify-center mx-auto">
                      <CheckCircle2 className="w-10 h-10 text-green-500" />
                    </div>
                    <div className="absolute inset-0 w-20 h-20 rounded-full border-2 border-green-500/30 animate-ping mx-auto" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold">Report Ready!</h3>
                    <p className="text-muted-foreground">
                      Your property report has been generated successfully.
                    </p>
                  </div>
                  <div className="flex gap-3 justify-center">
                    <Button variant="outline" onClick={() => router.push("/app/property")}>
                      View All Reports
                    </Button>
                    <Button onClick={() => router.push(`/app/property/${generatedReportId}`)}>
                      View Report
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

