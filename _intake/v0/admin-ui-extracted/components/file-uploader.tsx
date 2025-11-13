"use client"

import * as React from "react"
import { Upload, X, File } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface FileUploaderProps {
  onFileSelect: (files: File[]) => void
  accept?: string
  multiple?: boolean
  maxSize?: number // in MB
  className?: string
}

export function FileUploader({ onFileSelect, accept, multiple = false, maxSize = 10, className }: FileUploaderProps) {
  const [files, setFiles] = React.useState<File[]>([])
  const [isDragging, setIsDragging] = React.useState(false)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const handleFiles = (newFiles: FileList | null) => {
    if (!newFiles) return

    const fileArray = Array.from(newFiles).filter((file) => file.size <= maxSize * 1024 * 1024)

    setFiles(multiple ? [...files, ...fileArray] : fileArray)
    onFileSelect(fileArray)
  }

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index)
    setFiles(newFiles)
    onFileSelect(newFiles)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "glass rounded-xl border-2 border-dashed border-border p-8 text-center transition-all duration-200 cursor-pointer hover:border-primary/50",
          isDragging && "border-primary bg-primary/5",
        )}
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="w-10 h-10 mx-auto mb-4 text-muted-foreground" />
        <p className="font-display font-medium mb-1">Drop files here or click to upload</p>
        <p className="text-sm text-muted-foreground">
          {accept ? `Accepts: ${accept}` : "Any file type"} • Max {maxSize}MB
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFiles(e.target.files)}
          className="hidden"
        />
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, index) => (
            <div key={index} className="glass rounded-lg border border-border p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                  <File className="w-4 h-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => {
                  e.stopPropagation()
                  removeFile(index)
                }}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
