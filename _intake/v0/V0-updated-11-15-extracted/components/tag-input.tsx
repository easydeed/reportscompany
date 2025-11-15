"use client"

import { cn } from "@/lib/utils"
import { X } from "lucide-react"
import { useState, type KeyboardEvent } from "react"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

interface TagInputProps {
  tags: string[]
  onTagsChange: (tags: string[]) => void
  placeholder?: string
  validate?: (tag: string) => boolean
  className?: string
}

export function TagInput({
  tags,
  onTagsChange,
  placeholder = "Type and press Enter...",
  validate,
  className,
}: TagInputProps) {
  const [input, setInput] = useState("")
  const [error, setError] = useState(false)

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && input.trim()) {
      e.preventDefault()
      const trimmed = input.trim()

      if (validate && !validate(trimmed)) {
        setError(true)
        setTimeout(() => setError(false), 2000)
        return
      }

      if (!tags.includes(trimmed)) {
        onTagsChange([...tags, trimmed])
        setInput("")
      }
    } else if (e.key === "Backspace" && !input && tags.length > 0) {
      onTagsChange(tags.slice(0, -1))
    }
  }

  const removeTag = (tagToRemove: string) => {
    onTagsChange(tags.filter((tag) => tag !== tagToRemove))
  }

  return (
    <div
      className={cn(
        "flex flex-wrap gap-2 p-3 rounded-lg border bg-background transition-all duration-180",
        error
          ? "border-danger ring-2 ring-danger/20"
          : "border-input focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20",
        className,
      )}
    >
      {tags.map((tag) => (
        <Badge
          key={tag}
          variant="secondary"
          className="pl-3 pr-1 py-1 gap-1.5 rounded-md bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
        >
          <span className="text-sm">{tag}</span>
          <button
            type="button"
            onClick={() => removeTag(tag)}
            className="rounded-sm hover:bg-primary/20 p-0.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
            aria-label={`Remove ${tag}`}
          >
            <X className="w-3 h-3" />
          </button>
        </Badge>
      ))}
      <Input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[120px] border-0 p-0 h-auto focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent"
      />
    </div>
  )
}
