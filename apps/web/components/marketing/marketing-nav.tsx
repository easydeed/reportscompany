"use client"

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Menu, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { Logo } from "@/components/logo"

export function MarketingNav() {
  const [isScrolled, setIsScrolled] = React.useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false)

  React.useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 10)
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const scrollTo = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault()
    const el = document.getElementById(id)
    if (el) {
      const offset = el.getBoundingClientRect().top + window.pageYOffset - 72
      window.scrollTo({ top: offset, behavior: "smooth" })
    }
    setIsMobileMenuOpen(false)
  }

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled
          ? "bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm"
          : "bg-transparent"
      )}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-[72px]">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <Logo variant="full" className="h-9" />
          </Link>

          {/* Desktop: simple flat links */}
          <div className="hidden lg:flex items-center gap-8">
            <a
              href="#pricing"
              onClick={(e) => scrollTo(e, "pricing")}
              className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
            >
              Pricing
            </a>
            <Link
              href="/login"
              className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
            >
              Login
            </Link>
            <Button
              className="rounded-full bg-indigo-500 hover:bg-indigo-600 text-white px-6 shadow-sm hover:shadow-md transition-all"
              asChild
            >
              <Link href="/register">Start free →</Link>
            </Button>
          </div>

          {/* Mobile hamburger */}
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden text-slate-900 hover:bg-slate-100"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="lg:hidden bg-white border-t border-slate-200"
          >
            <div className="px-4 py-6 space-y-4">
              <a
                href="#pricing"
                onClick={(e) => scrollTo(e, "pricing")}
                className="block text-sm font-medium text-slate-600 hover:text-slate-900 py-2 cursor-pointer"
              >
                Pricing
              </a>
              <Link
                href="/login"
                className="block text-sm font-medium text-slate-600 hover:text-slate-900 py-2"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Login
              </Link>
              <Button
                className="w-full rounded-full bg-indigo-500 hover:bg-indigo-600 text-white"
                asChild
              >
                <Link
                  href="/register"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Start free →
                </Link>
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
