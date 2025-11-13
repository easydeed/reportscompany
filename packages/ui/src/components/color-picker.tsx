"use client"
import { Label } from "./ui/label"
import { Input } from "./ui/input"
import { cn } from "../lib/utils"

interface ColorPickerProps {
  label: string
  value: string
  onChange: (color: string) => void
  className?: string
}

export function ColorPicker({ label, value, onChange, className }: ColorPickerProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label className="font-display font-medium">{label}</Label>
      <div className="flex gap-2">
        <div className="relative">
          <input
            type="color"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-12 h-10 rounded-lg cursor-pointer border-2 border-border"
          />
        </div>
        <Input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
          className="flex-1 font-mono"
        />
      </div>
    </div>
  )
}
