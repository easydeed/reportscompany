"use client"

import { Card, CardContent } from "@/components/ui/card"
import { User } from "lucide-react"

interface BrandingPreviewProps {
  brandDisplayName?: string
  logoUrl?: string
  primaryColor?: string
  accentColor?: string
  repPhotoUrl?: string
  contactLine1?: string
  contactLine2?: string
  websiteUrl?: string
}

export function BrandingPreview({
  brandDisplayName = "Your Company Name",
  logoUrl,
  primaryColor = "#4F46E5",
  accentColor = "#F26B2B",
  repPhotoUrl,
  contactLine1 = "Your Name | (555) 123-4567",
  contactLine2 = "your@email.com",
  websiteUrl,
}: BrandingPreviewProps) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {/* Mini Report Preview */}
        <div className="bg-white text-black text-xs">
          {/* Header */}
          <div 
            className="p-3 flex items-center justify-between"
            style={{ backgroundColor: primaryColor }}
          >
            <div className="flex items-center gap-2">
              {logoUrl ? (
                <img 
                  src={logoUrl} 
                  alt="Logo" 
                  className="h-6 w-auto max-w-[80px] object-contain"
                  style={{ filter: "brightness(0) invert(1)" }}
                />
              ) : (
                <div className="h-6 w-16 bg-white/20 rounded flex items-center justify-center text-white/60 text-[8px]">
                  LOGO
                </div>
              )}
              <span className="text-white font-semibold text-[10px] truncate max-w-[100px]">
                {brandDisplayName}
              </span>
            </div>
            <span className="text-white/80 text-[8px]">Market Report</span>
          </div>

          {/* Content */}
          <div className="p-3 space-y-2">
            <div className="text-center">
              <div className="text-[10px] font-bold text-gray-800">Market Snapshot</div>
              <div className="text-[8px] text-gray-500">Irvine, CA • December 2025</div>
            </div>

            {/* Sample Stats */}
            <div className="grid grid-cols-3 gap-1">
              <div 
                className="rounded p-1.5 text-center"
                style={{ backgroundColor: `${primaryColor}10` }}
              >
                <div 
                  className="text-[10px] font-bold"
                  style={{ color: primaryColor }}
                >
                  $1.53M
                </div>
                <div className="text-[6px] text-gray-500">Median Price</div>
              </div>
              <div 
                className="rounded p-1.5 text-center"
                style={{ backgroundColor: `${primaryColor}10` }}
              >
                <div 
                  className="text-[10px] font-bold"
                  style={{ color: primaryColor }}
                >
                  45
                </div>
                <div className="text-[6px] text-gray-500">Avg DOM</div>
              </div>
              <div 
                className="rounded p-1.5 text-center"
                style={{ backgroundColor: `${primaryColor}10` }}
              >
                <div 
                  className="text-[10px] font-bold"
                  style={{ color: primaryColor }}
                >
                  3.2
                </div>
                <div className="text-[6px] text-gray-500">Months Inv.</div>
              </div>
            </div>

            {/* Sample Chart Placeholder */}
            <div className="h-8 bg-gray-100 rounded flex items-center justify-center">
              <div className="flex items-end gap-0.5 h-5">
                {[3, 5, 4, 6, 5, 7, 6].map((h, i) => (
                  <div 
                    key={i}
                    className="w-2 rounded-t"
                    style={{ 
                      height: `${h * 3}px`,
                      backgroundColor: i === 6 ? accentColor : primaryColor,
                      opacity: i === 6 ? 1 : 0.6
                    }}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div 
            className="p-2 flex items-center gap-2"
            style={{ backgroundColor: `${accentColor}15`, borderTop: `2px solid ${accentColor}` }}
          >
            {repPhotoUrl ? (
              <img 
                src={repPhotoUrl} 
                alt="Rep" 
                className="h-8 w-8 rounded-full object-cover border-2"
                style={{ borderColor: accentColor }}
              />
            ) : (
              <div 
                className="h-8 w-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${accentColor}30` }}
              >
                <User className="h-4 w-4" style={{ color: accentColor }} />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="text-[8px] font-semibold text-gray-800 truncate">
                {contactLine1}
              </div>
              <div className="text-[7px] text-gray-500 truncate">
                {contactLine2}
              </div>
              {websiteUrl && (
                <div 
                  className="text-[7px] truncate"
                  style={{ color: accentColor }}
                >
                  {websiteUrl.replace(/^https?:\/\//, '')}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

