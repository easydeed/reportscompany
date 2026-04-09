"use client"

import { useState, useMemo } from "react"
import {
  Rocket,
  FileText,
  Calendar,
  Users,
  Target,
  Palette,
  CreditCard,
  Building2,
  HelpCircle,
  Search,
  ChevronDown,
  ChevronUp,
  UserPlus,
  Mail,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { PageHeader } from "@/components/page-header"
import { cn } from "@/lib/utils"
import { HELP_SECTIONS, QUICK_START_ITEMS, type HelpSection, type HelpArticle } from "./help-content"

// ── Icon Resolver ──────────────────────────────────────

const ICON_MAP: Record<string, LucideIcon> = {
  Rocket,
  FileText,
  Calendar,
  Users,
  Target,
  Palette,
  CreditCard,
  Building2,
  HelpCircle,
  UserPlus,
  Mail,
}

function resolveIcon(name: string): LucideIcon {
  return ICON_MAP[name] || HelpCircle
}

// ── Workflow Guide Card ────────────────────────────────

function WorkflowGuideCard({ article }: { article: HelpArticle }) {
  const [isExpanded, setIsExpanded] = useState(false)
  if (!article.steps) return null

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden transition-shadow hover:shadow-md">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-5 text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h4 className="text-base font-semibold text-foreground">
              {article.title}
            </h4>
            {article.description && (
              <p className="mt-1 text-[13px] text-muted-foreground line-clamp-1">
                {article.description}
              </p>
            )}
            <div className="mt-3 flex items-center gap-2">
              {article.steps.map((_, i) => (
                <div key={i} className="flex items-center gap-1.5">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                    {i + 1}
                  </span>
                  {i < (article.steps?.length ?? 0) - 1 && (
                    <div className="h-px w-4 bg-border" />
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-border px-5 pb-5">
          <div className="mt-4 space-y-6">
            {article.steps.map((step, i) => (
              <div key={i} className="flex gap-4">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <h5 className="font-semibold text-foreground">{step.title}</h5>
                  <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                    {step.body}
                  </p>
                  {step.screenshot && (
                    <div className="mt-3 rounded-lg bg-muted p-4 text-center">
                      <div className="mx-auto h-32 w-full max-w-md rounded-md bg-muted-foreground/10 flex items-center justify-center">
                        <span className="text-xs text-muted-foreground">
                          Screenshot: {step.screenshot}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setIsExpanded(false)}
            className="mt-6 text-sm font-medium text-primary hover:text-primary/80"
          >
            Collapse guide
          </button>
        </div>
      )}
    </div>
  )
}

// ── Section Navigation Item ────────────────────────────

function SectionNavItem({
  section,
  isActive,
  articleSummary,
  onClick,
}: {
  section: HelpSection
  isActive: boolean
  articleSummary: string
  onClick: () => void
}) {
  const Icon = resolveIcon(section.icon)
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors",
        isActive
          ? "bg-primary/5 text-primary ring-1 ring-primary/20"
          : "text-muted-foreground hover:bg-muted/50"
      )}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0",
          isActive ? "text-primary" : "text-muted-foreground/60"
        )}
      />
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            "block text-sm font-medium truncate",
            isActive ? "text-primary" : "text-foreground"
          )}
        >
          {section.title}
        </span>
        <span className="text-[11px] text-muted-foreground">
          {articleSummary}
        </span>
      </div>
    </button>
  )
}

// ── Main Page ──────────────────────────────────────────

export default function HelpCenterPage() {
  const [activeSection, setActiveSection] = useState("getting-started")
  const [searchQuery, setSearchQuery] = useState("")

  const currentSection = HELP_SECTIONS.find((s) => s.id === activeSection)

  const filteredArticles = useMemo(() => {
    if (!searchQuery.trim()) return currentSection?.articles || []

    const query = searchQuery.toLowerCase()
    return HELP_SECTIONS.flatMap((s) => s.articles).filter((article) => {
      const searchable = [
        article.title,
        article.description,
        article.question,
        article.answer,
        ...(article.steps?.flatMap((s) => [s.title, s.body]) ?? []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return searchable.includes(query)
    })
  }, [currentSection, searchQuery])

  const guides = filteredArticles.filter((a) => a.type === "guide")
  const faqs = filteredArticles.filter((a) => a.type === "faq")

  function articleCount(section: HelpSection) {
    const g = section.articles.filter((a) => a.type === "guide").length
    const f = section.articles.filter((a) => a.type === "faq").length
    if (g > 0 && f > 0) return `${g} guide${g > 1 ? "s" : ""}, ${f} FAQ${f > 1 ? "s" : ""}`
    if (g > 0) return `${g} guide${g > 1 ? "s" : ""}`
    return `${f} FAQ${f > 1 ? "s" : ""}`
  }

  const isSearching = searchQuery.trim().length > 0

  return (
    <div className="space-y-5">
      <PageHeader
        title="Help Center"
        description="Guides, FAQs, and troubleshooting"
      />

      {/* Welcome Banner + Search */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] p-6">
        <h2 className="text-lg font-semibold text-foreground">How can we help?</h2>
        <div className="relative mt-3 max-w-xl">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search for guides, FAQs, and more..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 pl-10"
          />
        </div>

        {/* Quick Start Cards */}
        {!isSearching && (
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {QUICK_START_ITEMS.map((item) => {
              const Icon = resolveIcon(item.icon)
              return (
                <button
                  key={item.title}
                  onClick={() => setActiveSection(item.sectionId)}
                  className="group flex items-center gap-3 rounded-xl border border-border bg-card p-3.5 text-left transition-all hover:border-primary/30 hover:bg-primary/5"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {item.title}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Mobile Section Selector */}
      {!isSearching && (
        <div className="lg:hidden">
          <div className="flex flex-wrap gap-2">
            {HELP_SECTIONS.map((section) => {
              const Icon = resolveIcon(section.icon)
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors",
                    activeSection === section.id
                      ? "bg-primary/10 text-primary"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {section.title}
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Main Content: Side Nav + Articles */}
      <div className="flex gap-5">
        {/* In-page Section Nav (desktop only) */}
        {!isSearching && (
          <div className="hidden lg:block w-[200px] shrink-0">
            <div className="sticky top-4 space-y-1">
              {HELP_SECTIONS.map((section) => (
                <SectionNavItem
                  key={section.id}
                  section={section}
                  isActive={activeSection === section.id}
                  articleSummary={articleCount(section)}
                  onClick={() => setActiveSection(section.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Article Content */}
        <div className={cn("flex-1 min-w-0", isSearching && "w-full")}>
          {/* Section Header */}
          {!isSearching && currentSection && (() => {
            const SectionIcon = resolveIcon(currentSection.icon)
            return (
              <div className="flex items-center gap-2 mb-4">
                <SectionIcon className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">
                  {currentSection.title}
                </h2>
              </div>
            )
          })()}

          {isSearching && (
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                {filteredArticles.length} result{filteredArticles.length !== 1 ? "s" : ""} for &ldquo;{searchQuery}&rdquo;
              </p>
              <button
                onClick={() => setSearchQuery("")}
                className="text-sm font-medium text-primary hover:text-primary/80"
              >
                Clear search
              </button>
            </div>
          )}

          {/* Guides */}
          {guides.length > 0 && (
            <div>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground mb-3">
                Step-by-Step Guides
              </h3>
              <div className="space-y-3">
                {guides.map((article) => (
                  <WorkflowGuideCard key={article.id} article={article} />
                ))}
              </div>
            </div>
          )}

          {/* FAQs */}
          {faqs.length > 0 && (
            <div className={guides.length > 0 ? "mt-6" : ""}>
              <h3 className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground mb-3">
                Frequently Asked Questions
              </h3>
              <Accordion
                type="single"
                collapsible
                className="rounded-xl border border-border bg-card overflow-hidden shadow-[var(--shadow-card)]"
              >
                {faqs.map((faq) => (
                  <AccordionItem key={faq.id} value={faq.id}>
                    <AccordionTrigger className="px-5 py-4 text-left text-sm font-medium text-foreground hover:no-underline hover:bg-muted/30">
                      {faq.question}
                    </AccordionTrigger>
                    <AccordionContent className="px-5 text-sm text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          )}

          {/* Empty State */}
          {filteredArticles.length === 0 && (
            <div className="rounded-xl border border-border bg-card p-10 text-center shadow-[var(--shadow-card)]">
              <HelpCircle className="mx-auto h-10 w-10 text-muted-foreground/40" />
              <p className="mt-4 text-muted-foreground">
                No articles found matching &ldquo;{searchQuery}&rdquo;
              </p>
              <button
                onClick={() => setSearchQuery("")}
                className="mt-2 text-sm font-medium text-primary hover:text-primary/80"
              >
                Clear search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Still Need Help Footer */}
      <div className="bg-card border border-border rounded-xl shadow-[var(--shadow-card)] p-5">
        <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 shrink-0">
            <Mail className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-foreground">Still need help?</h3>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Can&apos;t find what you&apos;re looking for? Our support team is here to help.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" asChild>
              <a href="mailto:support@trendyreports.com" className="gap-2">
                <Mail className="h-3.5 w-3.5" />
                Contact Support
              </a>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
