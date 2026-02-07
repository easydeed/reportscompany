"use client";

import React from "react"

import { useState } from "react";
import {
  EmailHeader,
  GalleryHeader,
  TableHeader,
  AnalyticsHeader,
} from "@/components/email/email-header";
import { MarketSnapshot } from "@/components/email/market-snapshot";
import { ListingsGallery } from "@/components/email/listings-gallery";
import { TableView } from "@/components/email/table-view";
import { MarketAnalytics } from "@/components/email/market-analytics";
import { AgentFooter, EmailDisclaimer } from "@/components/email/email-footer";
import { BarChart3, Grid3X3, Table2, TrendingUp } from "lucide-react";

type Tab = "snapshot" | "gallery" | "table" | "analytics";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "snapshot", label: "Market Snapshot", icon: BarChart3 },
  { id: "gallery", label: "Listings Gallery", icon: Grid3X3 },
  { id: "table", label: "Table View", icon: Table2 },
  { id: "analytics", label: "Analytics", icon: TrendingUp },
];

const HEADERS: Record<Tab, React.ComponentType> = {
  snapshot: EmailHeader,
  gallery: GalleryHeader,
  table: TableHeader,
  analytics: AnalyticsHeader,
};

const BODIES: Record<Tab, React.ComponentType> = {
  snapshot: MarketSnapshot,
  gallery: ListingsGallery,
  table: TableView,
  analytics: MarketAnalytics,
};

export default function Page() {
  const [activeTab, setActiveTab] = useState<Tab>("snapshot");

  const HeaderComponent = HEADERS[activeTab];
  const BodyComponent = BODIES[activeTab];

  return (
    <main className="min-h-screen bg-background px-4 py-12">
      {/* Page Title */}
      <div className="mx-auto mb-8 max-w-[680px] text-center">
        <h1 className="font-serif text-3xl tracking-tight text-foreground">
          Email Template Preview
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Premium real estate market report email templates
        </p>
      </div>

      {/* Tab Switcher */}
      <div className="mx-auto mb-6 flex max-w-[680px] justify-center">
        <div className="inline-flex flex-wrap justify-center gap-1 rounded-xl border border-border bg-card p-1.5 shadow-sm">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                  isActive
                    ? "bg-[#1e3a5f] text-white shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Email Container */}
      <div className="mx-auto max-w-[600px] overflow-hidden rounded-lg border border-border bg-card shadow-lg">
        <HeaderComponent />
        <BodyComponent />
        <AgentFooter />
        <EmailDisclaimer />
      </div>

      {/* Bottom spacer */}
      <div className="h-12" />
    </main>
  );
}
