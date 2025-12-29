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
  title: 'Market Reports',
  description: 'MLS data. Beautiful reports. Zero effort.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`antialiased ${plusJakarta.variable}`}>
      <body className={`min-h-screen ${plusJakarta.className}`}>
        {children}
      </body>
    </html>
  );
}
