import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Market Reports',
  description: 'MLS data. Beautiful reports. Zero effort.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="antialiased">
      <body className="min-h-screen">
        {children}
      </body>
    </html>
  );
}
