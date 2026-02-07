"use client";

import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 bg-background/80 backdrop-blur-md transition-shadow duration-300 ${scrolled ? "shadow-sm" : ""}`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="#" className="text-xl font-bold text-[#6366F1]">
          TrendyReports
        </a>

        {/* Desktop links */}
        <div className="hidden items-center gap-6 md:flex">
          <a
            href="#how-it-works"
            className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            How It Works
          </a>
          <a
            href="#reports"
            className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            Reports
          </a>
          <a
            href="#lead-capture"
            className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            Lead Capture
          </a>
          <a
            href="#contacts"
            className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            Contacts
          </a>
          <a
            href="#pricing"
            className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            Pricing
          </a>
          <a
            href="/login"
            className="text-sm font-medium text-foreground/70 transition-colors hover:text-foreground"
          >
            Log in
          </a>
          <a
            href="/register"
            className="inline-flex items-center rounded-full bg-[#6366F1] px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
          >
            Start free trial
          </a>
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          className="inline-flex items-center justify-center rounded-lg p-2 text-foreground md:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-border bg-background px-6 pb-6 pt-4 md:hidden">
          <div className="flex flex-col gap-4">
            <a
              href="#how-it-works"
              className="text-sm font-medium text-foreground/70"
              onClick={() => setMobileOpen(false)}
            >
              How It Works
            </a>
            <a
              href="#reports"
              className="text-sm font-medium text-foreground/70"
              onClick={() => setMobileOpen(false)}
            >
              Reports
            </a>
            <a
              href="#lead-capture"
              className="text-sm font-medium text-foreground/70"
              onClick={() => setMobileOpen(false)}
            >
              Lead Capture
            </a>
            <a
              href="#contacts"
              className="text-sm font-medium text-foreground/70"
              onClick={() => setMobileOpen(false)}
            >
              Contacts
            </a>
            <a
              href="#pricing"
              className="text-sm font-medium text-foreground/70"
              onClick={() => setMobileOpen(false)}
            >
              Pricing
            </a>
            <a
              href="/login"
              className="text-sm font-medium text-foreground/70"
              onClick={() => setMobileOpen(false)}
            >
              Log in
            </a>
            <a
              href="/register"
              className="inline-flex items-center justify-center rounded-full bg-[#6366F1] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#4F46E5]"
              onClick={() => setMobileOpen(false)}
            >
              Start free trial
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
