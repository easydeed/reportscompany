# Branding System Overhaul — Implementation Plan

**Project**: TrendyReports Affiliate Branding Enhancement  
**Date**: November 25, 2025  
**Objective**: Transform branding from basic URL inputs into a polished, professional white-label experience that makes affiliates look exceptional.

---

## Overview

This plan is divided into **5 Passes**, each building on the previous. Complete each pass fully before moving to the next. Each pass has clear acceptance criteria.

```
PASS B1: File Upload Infrastructure (Backend)
PASS B2: File Upload UI (Frontend)
PASS B3: Live Template Previews
PASS B4: Download & Test Send
PASS B5: Polish & Headshot Integration
```

---

## Pre-Flight Checklist

Before starting, verify these files exist and understand their purpose:

| File | Purpose | Action |
|------|---------|--------|
| `apps/api/src/api/routes/affiliates.py` | Affiliate API routes | Will add upload endpoint |
| `apps/api/src/api/services/branding.py` | Brand resolution logic | Will add upload service |
| `apps/web/app/app/branding/page.tsx` | Branding UI page | Will overhaul completely |
| `apps/web/lib/templates.ts` | Template injection | Will reference for previews |
| `apps/worker/src/worker/storage.py` | R2 upload utilities | Will reuse for branding assets |

**Environment Variables Needed** (should already exist for PDF storage):
```
R2_ACCOUNT_ID=xxx
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=xxx
R2_PUBLIC_URL=xxx
```

---

## PASS B1: File Upload Infrastructure (Backend)

**Goal**: Create API endpoint to upload logo/headshot files to R2 and return permanent URLs.

### B1.1: Create Upload Service

**File**: `apps/api/src/api/services/upload.py` (NEW)

```python
"""
Branding asset upload service.
Uploads images to Cloudflare R2 and returns public URLs.
"""

import boto3
import uuid
from datetime import datetime
from botocore.config import Config
from PIL import Image
import io
from fastapi import UploadFile, HTTPException

# Configuration from environment
import os

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

# Constraints
MAX_FILE_SIZE_MB = 5
ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_DIMENSIONS = (2000, 2000)
MIN_DIMENSIONS = (100, 100)


def get_r2_client():
    """Get configured R2 client."""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


async def validate_image(file: UploadFile) -> bytes:
    """
    Validate uploaded image file.
    Returns file bytes if valid, raises HTTPException if not.
    """
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: PNG, JPEG, WebP, GIF"
        )
    
    # Read file
    contents = await file.read()
    
    # Check file size
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB"
        )
    
    # Check dimensions using PIL
    try:
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
        
        if width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]:
            raise HTTPException(
                status_code=400,
                detail=f"Image too small. Minimum: {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}px"
            )
        
        if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}px"
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    return contents


async def upload_branding_asset(
    file: UploadFile,
    account_id: str,
    asset_type: str  # "logo" or "headshot"
) -> str:
    """
    Upload a branding asset to R2.
    Returns the public URL of the uploaded file.
    """
    # Validate
    contents = await validate_image(file)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"branding/{account_id}/{asset_type}_{timestamp}_{unique_id}.{ext}"
    
    # Upload to R2
    client = get_r2_client()
    client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=filename,
        Body=contents,
        ContentType=file.content_type,
        CacheControl="public, max-age=31536000",  # 1 year cache
    )
    
    # Return public URL
    public_url = f"{R2_PUBLIC_URL}/{filename}"
    return public_url


async def delete_branding_asset(url: str) -> bool:
    """
    Delete a branding asset from R2 by URL.
    Returns True if deleted, False if not found.
    """
    if not url or not url.startswith(R2_PUBLIC_URL):
        return False
    
    # Extract key from URL
    key = url.replace(f"{R2_PUBLIC_URL}/", "")
    
    try:
        client = get_r2_client()
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        return True
    except Exception:
        return False
```

### B1.2: Create Upload API Endpoint

**File**: `apps/api/src/api/routes/upload.py` (NEW)

```python
"""
File upload routes for branding assets.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel

from api.middleware.authn import get_current_account
from api.services.upload import upload_branding_asset

router = APIRouter(prefix="/v1/upload", tags=["upload"])


class UploadResponse(BaseModel):
    url: str
    filename: str
    size_bytes: int


@router.post("/branding/{asset_type}", response_model=UploadResponse)
async def upload_branding_file(
    asset_type: str,
    file: UploadFile = File(...),
    account = Depends(get_current_account)
):
    """
    Upload a branding asset (logo or headshot).
    
    - asset_type: "logo" or "headshot"
    - file: Image file (PNG, JPEG, WebP, GIF; max 5MB; 100-2000px)
    
    Returns the public URL of the uploaded file.
    """
    if asset_type not in ("logo", "headshot"):
        raise HTTPException(status_code=400, detail="asset_type must be 'logo' or 'headshot'")
    
    # Get file size before upload (need to read then reset)
    contents = await file.read()
    size_bytes = len(contents)
    await file.seek(0)  # Reset for upload function
    
    url = await upload_branding_asset(file, str(account.id), asset_type)
    
    return UploadResponse(
        url=url,
        filename=file.filename,
        size_bytes=size_bytes
    )
```

### B1.3: Register Upload Routes

**File**: `apps/api/src/api/main.py`

Add to router includes:
```python
from api.routes.upload import router as upload_router

# In create_app() or wherever routers are registered:
app.include_router(upload_router)
```

### B1.4: Add PIL Dependency

**File**: `apps/api/pyproject.toml`

Add to dependencies:
```toml
Pillow = "^10.0.0"
```

Then run: `poetry lock && poetry install`

### B1.5: Frontend Proxy Route

**File**: `apps/web/app/api/proxy/v1/upload/branding/[assetType]/route.ts` (NEW)

```typescript
import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://reportscompany.onrender.com";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ assetType: string }> }
) {
  const { assetType } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get("mr_token")?.value;

  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Forward the multipart form data
  const formData = await request.formData();

  const response = await fetch(`${API_URL}/v1/upload/branding/${assetType}`, {
    method: "POST",
    headers: {
      Cookie: `mr_token=${token}`,
    },
    body: formData,
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
```

### B1 Acceptance Criteria

- [ ] `POST /v1/upload/branding/logo` accepts image file, returns URL
- [ ] `POST /v1/upload/branding/headshot` accepts image file, returns URL
- [ ] Invalid file types rejected with clear error
- [ ] Oversized files rejected with clear error
- [ ] Uploaded files accessible at returned URL
- [ ] Files stored in `branding/{account_id}/` path in R2

**Test Command**:
```bash
curl -X POST \
  -H "Cookie: mr_token=YOUR_TOKEN" \
  -F "file=@test-logo.png" \
  https://reportscompany.onrender.com/v1/upload/branding/logo
```

---

## PASS B2: File Upload UI (Frontend)

**Goal**: Replace URL text inputs with drag-and-drop file upload components.

### B2.1: Create ImageUpload Component

**File**: `apps/web/components/ui/image-upload.tsx` (NEW)

```tsx
"use client";

import { useState, useCallback } from "react";
import { Upload, X, Loader2, AlertCircle } from "lucide-react";
import Image from "next/image";

interface ImageUploadProps {
  label: string;
  value: string | null;
  onChange: (url: string | null) => void;
  assetType: "logo" | "headshot";
  aspectRatio?: "square" | "wide" | "portrait";
  maxSizeMB?: number;
  helpText?: string;
}

export function ImageUpload({
  label,
  value,
  onChange,
  assetType,
  aspectRatio = "wide",
  maxSizeMB = 5,
  helpText,
}: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const aspectClasses = {
    square: "aspect-square",
    wide: "aspect-[3/1]",
    portrait: "aspect-[3/4]",
  };

  const handleUpload = useCallback(
    async (file: File) => {
      setError(null);
      setIsUploading(true);

      // Client-side validation
      if (!file.type.startsWith("image/")) {
        setError("Please upload an image file");
        setIsUploading(false);
        return;
      }

      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File too large. Maximum: ${maxSizeMB}MB`);
        setIsUploading(false);
        return;
      }

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`/api/proxy/v1/upload/branding/${assetType}`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Upload failed");
        }

        const data = await response.json();
        onChange(data.url);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [assetType, maxSizeMB, onChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleUpload(file);
    },
    [handleUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleUpload(file);
    },
    [handleUpload]
  );

  const handleRemove = useCallback(() => {
    onChange(null);
    setError(null);
  }, [onChange]);

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      
      {value ? (
        // Show uploaded image
        <div className="relative group">
          <div className={`relative ${aspectClasses[aspectRatio]} bg-gray-100 rounded-lg overflow-hidden border-2 border-gray-200`}>
            <Image
              src={value}
              alt={label}
              fill
              className="object-contain"
              unoptimized // External R2 URLs
            />
          </div>
          <button
            onClick={handleRemove}
            className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
            title="Remove"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        // Show upload zone
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`
            relative ${aspectClasses[aspectRatio]} border-2 border-dashed rounded-lg
            flex flex-col items-center justify-center cursor-pointer
            transition-colors
            ${isDragging ? "border-purple-500 bg-purple-50" : "border-gray-300 hover:border-gray-400"}
            ${isUploading ? "pointer-events-none" : ""}
          `}
        >
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={isUploading}
          />
          
          {isUploading ? (
            <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
          ) : (
            <>
              <Upload className="w-8 h-8 text-gray-400 mb-2" />
              <span className="text-sm text-gray-500">
                Drop image here or click to upload
              </span>
              <span className="text-xs text-gray-400 mt-1">
                PNG, JPEG, WebP • Max {maxSizeMB}MB
              </span>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {helpText && !error && (
        <p className="text-xs text-gray-500">{helpText}</p>
      )}
    </div>
  );
}
```

### B2.2: Update Branding Page

**File**: `apps/web/app/app/branding/page.tsx`

Replace the entire file with a new implementation. Key changes:

1. Replace logo URL text input with `<ImageUpload assetType="logo" />`
2. Replace headshot URL text input with `<ImageUpload assetType="headshot" />`
3. Add tabbed interface: "Brand Identity" | "Preview Reports" | "Download"
4. Keep existing color pickers and text inputs
5. Improve layout with better visual hierarchy

```tsx
"use client";

import { useState, useEffect } from "react";
import { ImageUpload } from "@/components/ui/image-upload";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Save, Loader2 } from "lucide-react";

// ... rest of implementation (see full file structure below)
```

### B2.3: Branding Page Full Structure

The new branding page should have this structure:

```
/app/branding
├── Brand Identity Tab
│   ├── Logo Upload (ImageUpload component)
│   ├── Brand Display Name (text input)
│   ├── Primary Color (color picker + hex)
│   ├── Accent Color (color picker + hex)
│   ├── [If Affiliate]
│   │   ├── Rep Photo Upload (ImageUpload component)
│   │   ├── Contact Line 1 (text input)
│   │   ├── Contact Line 2 (text input)
│   │   └── Website URL (text input)
│   └── Save Button
│
├── Preview Reports Tab (PASS B3)
│   ├── Report Type Selector (dropdown)
│   ├── Live Preview (iframe/rendered template)
│   └── Preview refreshes on branding changes
│
└── Download Tab (PASS B4)
    ├── Download Sample PDF Button
    └── Send Test Email Button
```

### B2 Acceptance Criteria

- [ ] Logo can be uploaded via drag-and-drop or click
- [ ] Headshot can be uploaded via drag-and-drop or click
- [ ] Upload shows loading spinner during upload
- [ ] Upload errors display clearly
- [ ] Uploaded images display in the form
- [ ] Images can be removed (X button)
- [ ] Form saves correctly with uploaded URLs
- [ ] Old URL-only inputs still work if user pastes a URL

---

## PASS B3: Live Template Previews

**Goal**: Show affiliates exactly how their branding appears on actual reports.

### B3.1: Create Sample Data Module

**File**: `apps/web/lib/sample-report-data.ts` (NEW)

```typescript
/**
 * Sample data for branding previews.
 * Uses realistic Beverly Hills data for impressive demos.
 */

export const SAMPLE_REPORT_DATA = {
  market_snapshot: {
    city: "Beverly Hills",
    state: "CA",
    lookback_days: 30,
    generated_at: new Date().toISOString(),
    counts: {
      Active: 127,
      Pending: 34,
      Closed: 89,
    },
    metrics: {
      median_list_price: 4250000,
      median_close_price: 4150000,
      avg_dom: 42,
      median_dom: 35,
      median_ppsf: 1285,
      months_of_inventory: 4.3,
      list_to_close_ratio: 0.976,
    },
    listings_sample: [
      {
        address: "1234 Sunset Blvd",
        city: "Beverly Hills",
        price: 5250000,
        beds: 5,
        baths: 6,
        sqft: 4800,
        status: "Active",
        dom: 12,
        photo_url: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800",
      },
      {
        address: "567 Rodeo Drive",
        city: "Beverly Hills",
        price: 3850000,
        beds: 4,
        baths: 4,
        sqft: 3200,
        status: "Pending",
        dom: 28,
        photo_url: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800",
      },
      // Add 4-6 more sample listings
    ],
  },
  
  new_listings: {
    // Similar structure with new listings focus
  },
  
  // ... other report types
};

export type ReportType = keyof typeof SAMPLE_REPORT_DATA;
export const REPORT_TYPES: { value: ReportType; label: string }[] = [
  { value: "market_snapshot", label: "Market Snapshot" },
  { value: "new_listings", label: "New Listings" },
  { value: "new_listings_gallery", label: "New Listings Gallery" },
  { value: "featured_listings", label: "Featured Listings" },
  { value: "inventory", label: "Inventory" },
  { value: "closed", label: "Closed Sales" },
  { value: "price_bands", label: "Price Bands" },
  { value: "open_houses", label: "Open Houses" },
];
```

### B3.2: Create Preview Component

**File**: `apps/web/components/branding/report-preview.tsx` (NEW)

```tsx
"use client";

import { useState, useMemo } from "react";
import { SAMPLE_REPORT_DATA, REPORT_TYPES, ReportType } from "@/lib/sample-report-data";
import { injectBrand } from "@/lib/templates";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Monitor, Smartphone, Tablet } from "lucide-react";

interface BrandingData {
  brand_display_name: string;
  logo_url: string | null;
  primary_color: string;
  accent_color: string;
  contact_line1?: string;
  contact_line2?: string;
  website_url?: string;
  rep_photo_url?: string | null;
}

interface ReportPreviewProps {
  branding: BrandingData;
}

export function ReportPreview({ branding }: ReportPreviewProps) {
  const [reportType, setReportType] = useState<ReportType>("market_snapshot");
  const [viewMode, setViewMode] = useState<"desktop" | "tablet" | "mobile">("desktop");

  const viewWidths = {
    desktop: "100%",
    tablet: "768px",
    mobile: "375px",
  };

  // Generate preview HTML
  const previewHtml = useMemo(() => {
    const data = SAMPLE_REPORT_DATA[reportType];
    // Load base template and inject branding + sample data
    // This will use the same template engine as production
    return generatePreviewHtml(reportType, data, branding);
  }, [reportType, branding]);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <Select value={reportType} onValueChange={(v) => setReportType(v as ReportType)}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select report type" />
          </SelectTrigger>
          <SelectContent>
            {REPORT_TYPES.map((type) => (
              <SelectItem key={type.value} value={type.value}>
                {type.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex items-center gap-1 border rounded-lg p-1">
          <button
            onClick={() => setViewMode("desktop")}
            className={`p-2 rounded ${viewMode === "desktop" ? "bg-purple-100 text-purple-700" : "text-gray-500"}`}
          >
            <Monitor className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode("tablet")}
            className={`p-2 rounded ${viewMode === "tablet" ? "bg-purple-100 text-purple-700" : "text-gray-500"}`}
          >
            <Tablet className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode("mobile")}
            className={`p-2 rounded ${viewMode === "mobile" ? "bg-purple-100 text-purple-700" : "text-gray-500"}`}
          >
            <Smartphone className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Preview Frame */}
      <div className="border rounded-lg bg-gray-100 p-4 overflow-auto" style={{ height: "600px" }}>
        <div
          className="bg-white shadow-lg mx-auto transition-all duration-300"
          style={{ width: viewWidths[viewMode], minHeight: "100%" }}
        >
          <iframe
            srcDoc={previewHtml}
            className="w-full h-full border-0"
            style={{ minHeight: "800px" }}
            title="Report Preview"
          />
        </div>
      </div>
    </div>
  );
}

function generatePreviewHtml(
  reportType: ReportType,
  data: any,
  branding: BrandingData
): string {
  // This function will:
  // 1. Load the HTML template for the report type
  // 2. Inject branding (colors, logo, name)
  // 3. Inject sample data
  // 4. Return complete HTML string
  
  // For now, return a placeholder that shows branding is applied
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        :root {
          --brand-primary: ${branding.primary_color};
          --brand-accent: ${branding.accent_color};
        }
        body { font-family: system-ui, sans-serif; margin: 0; padding: 20px; }
        .header { 
          background: ${branding.primary_color}; 
          color: white; 
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .logo { height: 50px; }
        .brand-name { font-size: 24px; font-weight: bold; }
        .content { padding: 20px; }
        .metric { 
          background: ${branding.accent_color}15;
          border-left: 4px solid ${branding.accent_color};
          padding: 16px;
          margin: 12px 0;
        }
      </style>
    </head>
    <body>
      <div class="header">
        ${branding.logo_url ? `<img src="${branding.logo_url}" class="logo" alt="Logo" />` : ""}
        <span class="brand-name">${branding.brand_display_name || "Your Brand"}</span>
      </div>
      <div class="content">
        <h1>Market Snapshot</h1>
        <p>Beverly Hills, CA • Last 30 Days</p>
        <div class="metric">
          <strong>Median Price:</strong> $4,150,000
        </div>
        <div class="metric">
          <strong>Active Listings:</strong> 127
        </div>
        <div class="metric">
          <strong>Days on Market:</strong> 35
        </div>
        <p style="margin-top: 40px; color: #666; font-size: 12px;">
          ${branding.contact_line1 || ""}<br/>
          ${branding.contact_line2 || ""}<br/>
          ${branding.website_url || ""}
        </p>
      </div>
    </body>
    </html>
  `;
}
```

### B3.3: Email Preview Component

**File**: `apps/web/components/branding/email-preview.tsx` (NEW)

Similar structure to report preview, but renders the email template instead.

### B3 Acceptance Criteria

- [ ] Report type dropdown shows all 8 report types
- [ ] Preview updates immediately when branding changes
- [ ] Preview shows correct colors from color pickers
- [ ] Preview shows uploaded logo
- [ ] Desktop/tablet/mobile toggle works
- [ ] Preview is scrollable for long reports
- [ ] Preview loads within 500ms of branding change

---

## PASS B4: Download & Test Send

**Goal**: Allow affiliates to download branded samples and send test emails.

### B4.1: Download Sample PDF Endpoint

**File**: `apps/api/src/api/routes/branding.py` (NEW or add to affiliates.py)

```python
@router.post("/v1/branding/sample-pdf")
async def generate_sample_pdf(
    report_type: str = "market_snapshot",
    account = Depends(get_current_account),
    db = Depends(get_db)
):
    """
    Generate a sample branded PDF for preview/download.
    Uses sample data, not real MLS data.
    """
    # 1. Get account's branding
    # 2. Load sample data for report_type
    # 3. Generate PDF using same pipeline as real reports
    # 4. Return PDF file (not stored in R2)
    
    from fastapi.responses import StreamingResponse
    import io
    
    # Generate PDF bytes
    pdf_bytes = await generate_branded_sample(account.id, report_type, db)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="sample-{report_type}.pdf"'
        }
    )
```

### B4.2: Test Email Endpoint

**File**: `apps/api/src/api/routes/branding.py`

```python
@router.post("/v1/branding/test-email")
async def send_test_email(
    email: str,  # Where to send
    report_type: str = "market_snapshot",
    account = Depends(get_current_account),
    db = Depends(get_db)
):
    """
    Send a test branded email to the specified address.
    Uses sample data, not real MLS data.
    """
    # 1. Validate email belongs to account (security)
    # 2. Get account's branding
    # 3. Generate sample report data
    # 4. Send via email service
    # 5. Return success/failure
    
    return {"status": "sent", "to": email}
```

### B4.3: Frontend Download Button

```tsx
function DownloadSection({ branding }: { branding: BrandingData }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportType, setReportType] = useState("market_snapshot");

  const handleDownload = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch("/api/proxy/v1/branding/sample-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_type: reportType }),
      });
      
      if (!response.ok) throw new Error("Failed to generate PDF");
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sample-${reportType}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      // Show error toast
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="font-medium">Download Sample Report</h3>
      <p className="text-sm text-gray-500">
        Download a sample PDF to see exactly how your branding appears.
      </p>
      <div className="flex gap-4">
        <Select value={reportType} onValueChange={setReportType}>
          {/* Report type options */}
        </Select>
        <Button onClick={handleDownload} disabled={isGenerating}>
          {isGenerating ? <Loader2 className="animate-spin" /> : "Download PDF"}
        </Button>
      </div>
    </div>
  );
}
```

### B4 Acceptance Criteria

- [ ] "Download Sample PDF" generates and downloads a PDF
- [ ] Downloaded PDF has correct branding applied
- [ ] PDF generation takes < 10 seconds
- [ ] "Send Test Email" sends email to specified address
- [ ] Test email arrives with correct branding
- [ ] Error states handled gracefully

---

## PASS B5: Polish & Headshot Integration

**Goal**: Final polish, headshot display in templates, and UX refinements.

### B5.1: Add Headshot to Email Template

**File**: `apps/web/templates/email-base.html` (or wherever email template lives)

Add optional headshot display:

```html
{{#if brand.rep_photo_url}}
<div class="rep-section">
  <img src="{{brand.rep_photo_url}}" alt="Your Representative" class="rep-photo" />
  <div class="rep-info">
    <strong>{{brand.contact_line1}}</strong>
    <span>{{brand.contact_line2}}</span>
  </div>
</div>
{{/if}}
```

### B5.2: Add Headshot to PDF Footer

Similar addition to PDF templates.

### B5.3: Branding Page Polish

Final UX improvements:
- Success toast on save
- Unsaved changes warning
- Better mobile responsiveness
- Help tooltips on fields
- "Reset to defaults" option

### B5 Acceptance Criteria

- [ ] Headshot appears in email template (when provided)
- [ ] Headshot appears in PDF footer (when provided)
- [ ] Headshot display is optional (graceful when missing)
- [ ] All form interactions feel polished
- [ ] Mobile view works correctly
- [ ] No console errors

---

## Testing Checklist

### Manual QA Flow

1. **Fresh Affiliate Account**
   - [ ] Navigate to /app/branding
   - [ ] Upload logo via drag-and-drop
   - [ ] Upload headshot via file picker
   - [ ] Set custom colors
   - [ ] Fill all contact fields
   - [ ] Save successfully

2. **Preview Testing**
   - [ ] Switch to Preview tab
   - [ ] Select each of 8 report types
   - [ ] Verify branding appears correctly
   - [ ] Toggle desktop/tablet/mobile views
   - [ ] Verify responsive behavior

3. **Download Testing**
   - [ ] Download sample PDF
   - [ ] Verify PDF has correct branding
   - [ ] Verify PDF is valid/openable

4. **Email Testing**
   - [ ] Send test email to self
   - [ ] Verify email arrives
   - [ ] Verify email has correct branding
   - [ ] Verify headshot appears (if uploaded)

5. **Sponsored Agent View**
   - [ ] Login as sponsored agent
   - [ ] Generate a report
   - [ ] Verify affiliate's branding is applied
   - [ ] Verify agent cannot edit affiliate branding

---

## Rollback Plan

If issues arise:

1. **Upload failures**: Revert to URL-only input (keep ImageUpload component but allow manual URL entry as fallback)
2. **Preview broken**: Disable Preview tab, show "Coming Soon"
3. **Download broken**: Disable download button, show "Contact Support"

---

## Files Created/Modified Summary

### New Files
- `apps/api/src/api/services/upload.py`
- `apps/api/src/api/routes/upload.py`
- `apps/web/app/api/proxy/v1/upload/branding/[assetType]/route.ts`
- `apps/web/components/ui/image-upload.tsx`
- `apps/web/components/branding/report-preview.tsx`
- `apps/web/components/branding/email-preview.tsx`
- `apps/web/lib/sample-report-data.ts`

### Modified Files
- `apps/api/src/api/main.py` (register upload routes)
- `apps/api/pyproject.toml` (add Pillow)
- `apps/web/app/app/branding/page.tsx` (complete overhaul)
- `apps/web/templates/email-*.html` (headshot integration)
- `apps/web/templates/trendy-*.html` (headshot integration)

---

## Success Metrics

After implementation, affiliates should be able to:

1. ✅ Upload logo in < 30 seconds
2. ✅ See exactly how their branding looks on all report types
3. ✅ Download a sample PDF to share with their team
4. ✅ Send a test email to verify delivery
5. ✅ Feel confident their brand looks professional

**Target**: 90% reduction in "how do I upload my logo?" support tickets.
