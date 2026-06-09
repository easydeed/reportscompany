import './globals.css';
import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-jakarta',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'TrendyReports — Branded Real Estate Market Reports on Autopilot',
    template: '%s | TrendyReports',
  },
  description:
    'Turn live MLS data into branded market reports and property reports, delivered to your sphere automatically. Built for Southern California real estate agents.',
  keywords: [
    'real estate market reports',
    'CMA software',
    'real estate marketing automation',
    'MLS reports',
    'real estate agent tools',
    'Southern California real estate',
    'CRMLS reports',
    'branded property reports',
  ],
  metadataBase: new URL('https://www.trendyreports.io'),
  openGraph: {
    title: 'TrendyReports — Branded Real Estate Market Reports on Autopilot',
    description:
      'Turn live MLS data into branded market reports and property reports, delivered to your sphere automatically.',
    url: 'https://www.trendyreports.io',
    siteName: 'TrendyReports',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'TrendyReports — Branded real estate market reports on autopilot',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TrendyReports — Branded Real Estate Market Reports on Autopilot',
    description:
      'Turn live MLS data into branded market reports and property reports, delivered to your sphere automatically.',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: '48x48' },
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon-96x96.png', sizes: '96x96', type: 'image/png' },
    ],
    apple: '/apple-icon.png',
  },
  manifest: '/site.webmanifest',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`antialiased ${plusJakarta.variable}`}>
      <head />
      <body className={`min-h-screen ${plusJakarta.className}`}>
        {/* Google Maps API removed from root - now loaded on-demand in components that need it */}
        {children}
      </body>
    </html>
  );
}
