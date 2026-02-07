import React from "react"
import type { Metadata } from "next"
import {
  Oswald,
  Inter,
  Playfair_Display,
  Source_Sans_3,
  Cormorant_Garamond,
  Montserrat,
  Space_Grotesk,
  DM_Sans,
} from "next/font/google"

import "./globals.css"

const oswald = Oswald({ subsets: ["latin"], variable: "--font-oswald", weight: ["400", "500", "600", "700"] })
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair", weight: ["400", "500", "600", "700"] })
const sourceSans = Source_Sans_3({ subsets: ["latin"], variable: "--font-source-sans", weight: ["300", "400", "600", "700"] })
const cormorant = Cormorant_Garamond({ subsets: ["latin"], variable: "--font-cormorant", weight: ["400", "500", "600", "700"] })
const montserrat = Montserrat({ subsets: ["latin"], variable: "--font-montserrat", weight: ["400", "500", "600", "700", "800", "900"] })
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk", weight: ["400", "500", "600", "700"] })
const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans", weight: ["400", "500", "600", "700"] })

export const metadata: Metadata = {
  title: "TrendyReports - Property Report",
  description: "Seller Property Report — luxury real estate market analysis",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body
        className={`antialiased ${oswald.variable} ${inter.variable} ${playfair.variable} ${sourceSans.variable} ${cormorant.variable} ${montserrat.variable} ${spaceGrotesk.variable} ${dmSans.variable}`}
      >
        {children}
      </body>
    </html>
  )
}
