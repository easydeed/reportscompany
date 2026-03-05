"use client"

import { cn } from "@/lib/utils"
import { Check } from "lucide-react"
import { STORIES, type StoryType } from "./types"

interface StepStoryProps {
  selected: StoryType | null
  onSelect: (story: StoryType) => void
}

export function StepStory({ selected, onSelect }: StepStoryProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">What story do you want to tell?</h2>
        <p className="text-sm text-gray-500 mt-1">Choose the type of report to send your audience.</p>
      </div>

      <div className="grid gap-2.5">
        {STORIES.map((story) => {
          const active = selected === story.id
          return (
            <button
              key={story.id}
              onClick={() => onSelect(story.id)}
              className={cn(
                "group relative flex items-start gap-4 rounded-xl border-2 p-4 text-left transition-all",
                active
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-gray-200 hover:border-primary/40 hover:bg-gray-50/50"
              )}
            >
              <span className="text-2xl flex-shrink-0 mt-0.5">{story.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900">{story.title}</span>
                  {active && (
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                      <Check className="h-3 w-3 text-white" />
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{story.description}</p>
                <p className="text-[10px] text-gray-400 mt-1">Best for: {story.bestFor}</p>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
