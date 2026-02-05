"use client";

import { useState, useCallback } from "react";
import { Upload, X, Loader2, AlertCircle, ImageIcon } from "lucide-react";
import Image from "next/image";
import { cn } from "@/lib/utils";

interface ImageUploadProps {
  label: string;
  value: string | null;
  onChange: (url: string | null) => void;
  assetType: "logo" | "headshot";
  aspectRatio?: "square" | "wide" | "portrait";
  maxSizeMB?: number;
  helpText?: string;
  className?: string;
}

/**
 * ImageUpload Component
 * 
 * Drag-and-drop image upload with preview.
 * Uploads to R2 via /api/proxy/v1/upload/branding/{assetType}
 * 
 * Pass B2.1: File Upload UI
 */
export function ImageUpload({
  label,
  value,
  onChange,
  assetType,
  aspectRatio = "wide",
  maxSizeMB = 5,
  helpText,
  className,
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
        setError("Please upload an image file (PNG, JPEG, WebP, or GIF)");
        setIsUploading(false);
        return;
      }

      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File too large. Maximum size: ${maxSizeMB}MB`);
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

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || data.error || "Upload failed");
        }

        onChange(data.url);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        setError(message);
        console.error("[ImageUpload] Error:", err);
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

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleUpload(file);
      // Reset input so same file can be selected again
      e.target.value = "";
    },
    [handleUpload]
  );

  const handleRemove = useCallback(() => {
    onChange(null);
    setError(null);
  }, [onChange]);

  // Allow pasting URL directly (fallback for users who have external URLs)
  const handlePasteUrl = useCallback(() => {
    const url = prompt("Enter image URL:");
    if (url && url.startsWith("http")) {
      onChange(url);
      setError(null);
    }
  }, [onChange]);

  return (
    <div className={cn("space-y-2", className)}>
      <label className="block text-sm font-medium text-foreground">{label}</label>

      {value ? (
        // Show uploaded image
        <div className="relative group">
          <div
            className={cn(
              "relative bg-muted rounded-lg overflow-hidden border-2 border-border",
              aspectClasses[aspectRatio]
            )}
          >
            <Image
              src={value}
              alt={label}
              fill
              className="object-contain p-2"
              unoptimized // External R2 URLs
              onError={() => setError("Failed to load image")}
            />
          </div>
          <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleRemove}
              className="p-1.5 bg-destructive text-destructive-foreground rounded-full hover:bg-destructive/90 transition-colors shadow-md"
              title="Remove image"
              type="button"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="absolute bottom-2 left-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <p className="text-xs text-muted-foreground bg-background/80 backdrop-blur-sm rounded px-2 py-1 truncate">
              {value.length > 50 ? `...${value.slice(-47)}` : value}
            </p>
          </div>
        </div>
      ) : (
        // Show upload zone
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "relative border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all duration-200",
            aspectClasses[aspectRatio],
            isDragging
              ? "border-primary bg-primary/5 scale-[1.02]"
              : "border-muted-foreground/25 hover:border-muted-foreground/50 hover:bg-muted/50",
            isUploading && "pointer-events-none opacity-70"
          )}
        >
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={isUploading}
          />

          {isUploading ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <span className="text-sm text-muted-foreground">Uploading...</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 p-4">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                {isDragging ? (
                  <ImageIcon className="w-6 h-6 text-primary" />
                ) : (
                  <Upload className="w-6 h-6 text-muted-foreground" />
                )}
              </div>
              <div className="text-center">
                <span className="text-sm font-medium text-foreground">
                  {isDragging ? "Drop image here" : "Drop image or click to upload"}
                </span>
                <p className="text-xs text-muted-foreground mt-1">
                  PNG, JPEG, WebP, GIF • Max {maxSizeMB}MB
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* URL fallback button */}
      {!value && !isUploading && (
        <button
          type="button"
          onClick={handlePasteUrl}
          className="text-xs text-muted-foreground hover:text-foreground underline"
        >
          Or paste an image URL
        </button>
      )}

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Help text */}
      {helpText && !error && (
        <p className="text-xs text-muted-foreground">{helpText}</p>
      )}
    </div>
  );
}


