"use client"

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Menu, X, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { Logo } from "@/components/logo"

// Main navigation structure
const navLinks = [
  { 
    label: "Product", 
    href: "#how-it-works",
    children: [
      { label: "How It Works", href: "#how-it-works" },
      { label: "Email Reports", href: "#email-reports" },
      { label: "PDF Reports", href: "#pdf-reports" },
    ]
  },
  { 
    label: "Solutions", 
    href: "#for-agents",
    children: [
      { label: "For Agents", href: "#for-agents" },
      { label: "For Affiliates", href: "#for-affiliates" },
    ]
  },
  { label: "Pricing", href: "#pricing" },
  { 
    label: "Company", 
    href: "/about",
    children: [
      { label: "About Us", href: "/about" },
      { label: "Blog", href: "/blog" },
      { label: "Help Center", href: "/help" },
      { label: "Contact", href: "mailto:hello@trendyreports.com" },
    ]
  },
]

export function Navbar() {
  const [isScrolled, setIsScrolled] = React.useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false)
  const [openDropdown, setOpenDropdown] = React.useState<string | null>(null)

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Smooth scroll handler for anchor links
  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith('#')) {
      e.preventDefault()
      const targetId = href.replace('#', '')
      const element = document.getElementById(targetId)
      if (element) {
        const navHeight = 64
        const elementPosition = element.getBoundingClientRect().top
        const offsetPosition = elementPosition + window.pageYOffset - navHeight
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        })
      }
    }
    setIsMobileMenuOpen(false)
    setOpenDropdown(null)
  }

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-200",
        isScrolled ? "bg-white/95 backdrop-blur-lg border-b border-slate-200 shadow-sm" : "bg-white/80 backdrop-blur-sm",
      )}
    >
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <Logo variant="full" className="h-10" />
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => (
              <div 
                key={link.label} 
                className="relative"
                onMouseEnter={() => link.children && setOpenDropdown(link.label)}
                onMouseLeave={() => setOpenDropdown(null)}
              >
                {link.children ? (
                  <>
                    <button
                      className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors rounded-lg hover:bg-slate-100"
                    >
                      {link.label}
                      <ChevronDown className={cn(
                        "w-4 h-4 transition-transform duration-200",
                        openDropdown === link.label && "rotate-180"
                      )} />
                    </button>
                    
                    {/* Dropdown Menu */}
                    <AnimatePresence>
                      {openDropdown === link.label && (
                        <motion.div
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 8 }}
                          transition={{ duration: 0.15 }}
                          className="absolute top-full left-0 pt-2"
                        >
                          <div className="bg-white rounded-xl shadow-lg border border-slate-200 py-2 min-w-[180px]">
                            {link.children.map((child) => (
                              <a
                                key={child.href}
                                href={child.href}
                                onClick={(e) => handleNavClick(e, child.href)}
                                className="block px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors"
                              >
                                {child.label}
                              </a>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </>
                ) : (
                  <a
                    href={link.href}
                    onClick={(e) => handleNavClick(e, link.href)}
                    className="px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors rounded-lg hover:bg-slate-100 cursor-pointer"
                  >
                    {link.label}
                  </a>
                )}
              </div>
            ))}
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <Link 
              href="/login" 
              className="hidden lg:inline-flex text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors px-3 py-2"
            >
              Sign in
            </Link>
            <Button
              className="hidden lg:inline-flex bg-indigo-600 hover:bg-indigo-700 text-white border-0 shadow-sm hover:shadow-md transition-all"
              asChild
            >
              <Link href="/register">Start Free Trial</Link>
            </Button>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden text-slate-900 hover:bg-slate-100"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="lg:hidden bg-white border-t border-slate-200"
          >
            <div className="px-4 py-4 space-y-1">
              {navLinks.map((link) => (
                <div key={link.label}>
                  {link.children ? (
                    <div className="space-y-1">
                      <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                        {link.label}
                      </div>
                      {link.children.map((child) => (
                        <a
                          key={child.href}
                          href={child.href}
                          onClick={(e) => handleNavClick(e, child.href)}
                          className="block px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors rounded-lg hover:bg-slate-100 cursor-pointer"
                        >
                          {child.label}
                        </a>
                      ))}
                    </div>
                  ) : (
                    <a
                      href={link.href}
                      onClick={(e) => handleNavClick(e, link.href)}
                      className="block px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors rounded-lg hover:bg-slate-100 cursor-pointer"
                    >
                      {link.label}
                    </a>
                  )}
                </div>
              ))}
              
              <div className="pt-4 mt-4 border-t border-slate-200 space-y-2">
                <Link
                  href="/login"
                  className="block text-center px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors rounded-lg hover:bg-slate-100"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Sign in
                </Link>
                <Button
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white"
                  asChild
                >
                  <Link href="/register" onClick={() => setIsMobileMenuOpen(false)}>
                    Start Free Trial
                  </Link>
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  )
}
