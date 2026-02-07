import React from "react";
import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans, DM_Serif_Display } from "next/font/google";

import "./globals.css";

const jakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
});
const dmSerif = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-dm-serif",
});

export const metadata: Metadata = {
  title: "Real Estate Market Report Email Template",
  description:
    "Premium white-label real estate market report email templates for agents and brokerages.",
};

export const viewport: Viewport = {
  themeColor: "#1e3a5f",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${jakartaSans.variable} ${dmSerif.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
