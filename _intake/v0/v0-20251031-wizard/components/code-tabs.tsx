"use client"

import * as React from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Check, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface CodeTabsProps {
  pythonCode: string
  javascriptCode: string
  className?: string
}

export function CodeTabs({ pythonCode, javascriptCode, className }: CodeTabsProps) {
  const [copiedTab, setCopiedTab] = React.useState<string | null>(null)

  const copyToClipboard = (code: string, tab: string) => {
    navigator.clipboard.writeText(code)
    setCopiedTab(tab)
    setTimeout(() => setCopiedTab(null), 2000)
  }

  return (
    <Tabs defaultValue="python" className={cn("w-full", className)}>
      <TabsList className="grid w-full max-w-[400px] grid-cols-2">
        <TabsTrigger value="python" className="font-display">
          Python
        </TabsTrigger>
        <TabsTrigger value="javascript" className="font-display">
          JavaScript
        </TabsTrigger>
      </TabsList>
      <TabsContent value="python" className="relative">
        <div className="glass rounded-xl border border-border overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-secondary/50">
            <span className="text-xs font-medium text-muted-foreground font-display">Python</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(pythonCode, "python")}
              className="h-7 text-xs"
            >
              {copiedTab === "python" ? (
                <>
                  <Check className="w-3 h-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3 mr-1" />
                  Copy
                </>
              )}
            </Button>
          </div>
          <pre className="p-4 overflow-x-auto text-sm">
            <code className="text-foreground font-mono">{pythonCode}</code>
          </pre>
        </div>
      </TabsContent>
      <TabsContent value="javascript" className="relative">
        <div className="glass rounded-xl border border-border overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-secondary/50">
            <span className="text-xs font-medium text-muted-foreground font-display">JavaScript</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(javascriptCode, "javascript")}
              className="h-7 text-xs"
            >
              {copiedTab === "javascript" ? (
                <>
                  <Check className="w-3 h-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3 mr-1" />
                  Copy
                </>
              )}
            </Button>
          </div>
          <pre className="p-4 overflow-x-auto text-sm">
            <code className="text-foreground font-mono">{javascriptCode}</code>
          </pre>
        </div>
      </TabsContent>
    </Tabs>
  )
}
