import React from "react"
import type { Metadata, Viewport } from 'next'
import { Plus_Jakarta_Sans } from 'next/font/google'
import { Toaster } from "@/components/ui/sonner"

import './globals.css'

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-plus-jakarta',
})

export const metadata: Metadata = {
  title: 'TrendyReports — Beautiful market reports from live MLS data',
  description:
    'Create branded real estate market reports from live MLS data. Schedule email and PDF delivery on autopilot.',
}

export const viewport: Viewport = {
  themeColor: '#6366F1',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${plusJakarta.variable} font-sans antialiased`}>
        {children}
        <Toaster />
      </body>
    </html>
  )
}
