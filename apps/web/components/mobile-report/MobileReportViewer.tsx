'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, TrendingUp, BarChart3, User,
  Phone, MessageSquare, Mail, Download, Share2,
  ChevronLeft, ChevronRight, MapPin, Calendar,
  Bed, Bath, Square, Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Barlow, Barlow_Condensed, Cormorant_Garamond, Geist, Manrope } from 'next/font/google';
import { themeName } from '@/lib/themes.generated';

// Theme faces, as the PDF entry files set them
// (apps/worker/src/worker/templates/property/<theme>/<theme>_report.jinja2).
// Self-hosted through next/font; only the theme in use is painted.
const barlowCondensed = Barlow_Condensed({ subsets: ['latin'], weight: ['600', '700'], display: 'swap' });
const barlow = Barlow({ subsets: ['latin'], weight: ['400', '500', '600', '700'], display: 'swap' });
const cormorant = Cormorant_Garamond({ subsets: ['latin'], weight: ['500', '600'], display: 'swap' });
const geist = Geist({ subsets: ['latin'], weight: ['400', '500', '600', '700'], display: 'swap' });
const manrope = Manrope({ subsets: ['latin'], weight: ['400', '500', '600', '700', '800'], display: 'swap' });

type ThemeFaces = { display: string; body: string; weight: number; tracking: string; kase: string; radius: string };
const THEME_FACES: Record<string, ThemeFaces> = {
  atlas: { display: `${barlowCondensed.style.fontFamily}, "Arial Narrow", sans-serif`, body: `${barlow.style.fontFamily}, system-ui, sans-serif`, weight: 700, tracking: '0', kase: 'uppercase', radius: '4px' },
  linen: { display: `${cormorant.style.fontFamily}, Georgia, "Times New Roman", serif`, body: `${geist.style.fontFamily}, system-ui, sans-serif`, weight: 500, tracking: '-0.01em', kase: 'none', radius: '0px' },
  harbor: { display: `${manrope.style.fontFamily}, system-ui, sans-serif`, body: `${manrope.style.fontFamily}, system-ui, sans-serif`, weight: 800, tracking: '-0.035em', kase: 'none', radius: '14px' },
};

// The derive_theme tokens (apps/worker/src/worker/themes.py), read from the
// response. Until the API carries them the page renders on the one fixed dark
// neutral the PDF uses — readable everywhere, and visibly unbranded so nobody
// mistakes it for done.
type ThemeTokens = { primary: string; primary_dark: string; primary_ink: string; on_primary: string; tint: string; primary_on_dark: string; display_ink: string };
const NEUTRAL_TOKENS: ThemeTokens = { primary: '#0f172a', primary_dark: '#0c1221', primary_ink: '#0f172a', on_primary: '#ffffff', tint: '#f1f2f4', primary_on_dark: '#ffffff', display_ink: '#ffffff' };
import { NO_RANGE, RANGE_HEADING, compsSentence, homesSoldLabel, rangeBasis, type CompsRange, type ConsumerMarketStats } from "@/lib/consumer-report";

interface ReportData {
  id: string;
  property: {
    address: string;
    city: string;
    state: string;
    zip: string;
    bedrooms?: number;
    bathrooms?: number;
    sqft?: number;
    lot_size?: number;
    year_built?: number;
    latitude?: number;
    longitude?: number;
  };
  comparables: Array<{
    address: string;
    city: string;
    sold_price: number;
    sold_date: string;
    // D-168: null when the record has no value; printed as a dash.
    days_ago: number | null;
    bedrooms: number | null;
    bathrooms: number | null;
    sqft: number | null;
    price_per_sqft: number | null;
    distance_miles: number | null;
    photo_url?: string;
  }>;
  comps_range: CompsRange | null;
  market_stats: ConsumerMarketStats;
  agent: {
    name: string;
    phone?: string;
    email?: string;
    photo_url?: string;
    company_name?: string;
    license_number?: string;
  };
  branding?: {
    primary_color: string;
    accent_color: string;
    logo_url?: string;
  };
  theme?: number | null;
  theme_tokens?: ThemeTokens | null;
  has_pdf: boolean;
}

interface Props {
  report: ReportData;
  reportId: string;
}

type TabId = 'overview' | 'comps' | 'market' | 'agent';

const tabs: { id: TabId; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'comps', label: 'Comps', icon: TrendingUp },
  { id: 'market', label: 'Market', icon: BarChart3 },
  { id: 'agent', label: 'Agent', icon: User },
];

export function MobileReportViewer({ report, reportId }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [compIndex, setCompIndex] = useState(0);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [sessionId] = useState(() => Math.random().toString(36).slice(2));

  // Track tab views
  useEffect(() => {
    fetch(`/api/proxy/v1/r/${reportId}/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'tab_change',
        event_data: { tab: activeTab },
        session_id: sessionId,
      }),
    }).catch(() => {});
  }, [activeTab, reportId, sessionId]);

  const trackAgentClick = (type: string) => {
    fetch(`/api/proxy/v1/r/${reportId}/analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'agent_click',
        event_data: { contact_type: type },
        session_id: sessionId,
      }),
    }).catch(() => {});
  };

  const handleDownloadPdf = async () => {
    setPdfLoading(true);
    try {
      const res = await fetch(`/api/proxy/v1/r/${reportId}/pdf`, { method: 'POST' });
      const data = await res.json();
      
      if (data.status === 'ready') {
        setPdfUrl(data.pdf_url);
        window.open(data.pdf_url, '_blank');
        setPdfLoading(false);
      } else {
        // Poll for completion
        const checkPdf = async () => {
          // GET on the pdf proxy is the status check (D-314: /pdf/status had no route).
          const check = await fetch(`/api/proxy/v1/r/${reportId}/pdf`);
          const status = await check.json();
          if (status.status === 'ready') {
            setPdfUrl(status.pdf_url);
            setPdfLoading(false);
            window.open(status.pdf_url, '_blank');
          } else {
            setTimeout(checkPdf, 1000);
          }
        };
        checkPdf();
      }
    } catch (err) {
      console.error('PDF generation failed', err);
      setPdfLoading(false);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `Home Value Report - ${report.property.address}`,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    }
  };

  const formatPrice = (n: number) => `$${n.toLocaleString()}`;

  const tokens: ThemeTokens = report.theme_tokens ?? NEUTRAL_TOKENS;
  const faces: ThemeFaces = THEME_FACES[themeName(report.theme)];
  const themeVars = {
    '--primary': tokens.primary,
    '--primary-ink': tokens.primary_ink,
    '--on-primary': tokens.on_primary,
    '--tint': tokens.tint,
    '--primary-on-dark': tokens.primary_on_dark,
    '--display': faces.display,
    '--body-face': faces.body,
    '--display-weight': faces.weight,
    '--display-tracking': faces.tracking,
    '--display-case': faces.kase,
    '--radius': faces.radius,
  } as React.CSSProperties;

  return (
    <div className="min-h-screen flex flex-col" style={{ ...themeVars, background: '#F6F6F3', fontFamily: 'var(--body-face)', color: '#14161A', fontVariantNumeric: 'lining-nums' }}>
      {/* Header */}
      <header className="bg-white px-4 py-3 flex items-center justify-between sticky top-0 z-50" style={{ borderBottom: '1px solid #ECECE8' }}>
        <div className="flex-1 min-w-0 flex flex-col">
          <span style={{ fontSize: 10.5, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--primary-ink)', fontWeight: 600, whiteSpace: 'nowrap' }}>Home value report</span>
          <h1 className="truncate m-0" style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 22, lineHeight: 1.05, letterSpacing: 'var(--display-tracking)', textTransform: 'var(--display-case)' } as unknown as React.CSSProperties}>
            {report.property.address}
          </h1>
          <p className="m-0" style={{ fontSize: 12.5, color: '#5E636B' }}>
            {report.property.city}, {report.property.state} {report.property.zip}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={handleShare}>
          <Share2 className="w-5 h-5" />
        </Button>
      </header>

      {/* Tab Content */}
      <main className="flex-1 overflow-y-auto pb-20 w-full max-w-[560px] mx-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && (
              <OverviewTab report={report} formatPrice={formatPrice} />
            )}
            {activeTab === 'comps' && (
              <CompsTab 
                report={report} 
                compIndex={compIndex}
                setCompIndex={setCompIndex}
                formatPrice={formatPrice}
              />
            )}
            {activeTab === 'market' && (
              <MarketTab report={report} formatPrice={formatPrice} />
            )}
            {activeTab === 'agent' && (
              <AgentTab 
                report={report}
                onContactClick={trackAgentClick}
                onDownloadPdf={handleDownloadPdf}
                pdfLoading={pdfLoading}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Tab Bar */}
      <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[560px] bg-white flex justify-around z-50" style={{ borderTop: '1px solid #ECECE8' }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex flex-col items-center gap-[3px] px-2.5 pt-2.5 pb-2 min-w-[56px] -mt-px transition-colors"
              style={{ color: isActive ? 'var(--primary-ink)' : '#5E636B', fontWeight: isActive ? 600 : 500, borderTop: `2px solid ${isActive ? 'var(--primary)' : 'transparent'}` }}
            >
              <Icon className="w-5 h-5" />
              <span style={{ fontSize: 11.5 }}>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}


// =============================================
// TAB COMPONENTS
// =============================================

function OverviewTab({ report, formatPrice }: { report: ReportData; formatPrice: (n: number) => string }) {
  return (
    <div className="p-4 space-y-4">
      {/* Range panel — the PDF's page-4 panel on the fixed dark neutral; primary_on_dark is derived against it.
          Only the range, its method and its basis: no midpoint, no figure that isn't a comp. */}
      <div className="p-5 text-white flex flex-col gap-3" style={{ background: '#0f172a', borderRadius: 'var(--radius)' }}>
        <span style={{ fontSize: 10.5, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--primary-on-dark)', fontWeight: 600 }}>{RANGE_HEADING}</span>
        {report.comps_range ? (
          <>
            <span style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 34, lineHeight: 0.95, letterSpacing: 'var(--display-tracking)', textWrap: 'balance' } as React.CSSProperties}>
              {formatPrice(report.comps_range.low)} – {formatPrice(report.comps_range.high)}
            </span>
            <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)' }}>{report.comps_range.method}</span>
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)' }}>{rangeBasis(report.comps_range)}</span>
          </>
        ) : (
          <span style={{ fontSize: 15, lineHeight: 1.45 }}>{NO_RANGE}</span>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard 
          icon={<Bed className="w-5 h-5" />}
          label="Beds"
          value={report.property.bedrooms || '—'}
        />
        <StatCard 
          icon={<Bath className="w-5 h-5" />}
          label="Baths"
          value={report.property.bathrooms || '—'}
        />
        <StatCard 
          icon={<Square className="w-5 h-5" />}
          label="Sqft"
          value={report.property.sqft?.toLocaleString() || '—'}
        />
      </div>

      {/* Address card — plus the two facts the Details tab held that the tiles don't: lot size and year built, each once */}
      <div className="bg-white p-4 flex flex-col gap-3 rounded-[var(--radius)] border border-[#ECECE8]">
        <div className="flex items-start gap-3">
          <div>
            <p className="font-semibold text-gray-900">{report.property.address}</p>
            <p className="text-gray-600">
              {report.property.city}, {report.property.state} {report.property.zip}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 pt-3" style={{ borderTop: '1px solid #ECECE8' }}>
          <div className="flex flex-col gap-1">
            <p className="m-0" style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 20, lineHeight: 1, letterSpacing: 'var(--display-tracking)' } as React.CSSProperties}>
              {report.property.lot_size ? `${report.property.lot_size.toLocaleString()} sqft` : '—'}
            </p>
            <p className="m-0" style={{ fontSize: 11.5, color: '#5E636B' }}>Lot size</p>
          </div>
          <div className="flex flex-col gap-1">
            <p className="m-0" style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 20, lineHeight: 1, letterSpacing: 'var(--display-tracking)' } as React.CSSProperties}>
              {report.property.year_built || '—'}
            </p>
            <p className="m-0" style={{ fontSize: 11.5, color: '#5E636B' }}>Year built</p>
          </div>
        </div>
      </div>

      {/* Agent Preview */}
      <div className="bg-white p-4 rounded-[var(--radius)] border border-[#ECECE8]">
        <div className="flex items-center gap-3">
          {report.agent.photo_url ? (
            <img 
              src={report.agent.photo_url} 
              alt={report.agent.name}
              className="w-12 h-12 rounded-full object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'var(--tint)', color: 'var(--primary-ink)' }}>
              <User className="w-6 h-6" />
            </div>
          )}
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{report.agent.name}</p>
            <p className="text-sm text-gray-600">{report.agent.company_name}</p>
          </div>
          {report.agent.phone && (
            <a 
              href={`tel:${report.agent.phone.replace(/[\s().-]/g, '')}`}
              className="w-11 h-11 rounded-full flex items-center justify-center"
              style={{ background: 'var(--primary)', color: 'var(--on-primary)' }}
            >
              <Phone className="w-5 h-5" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}


function CompsTab({ 
  report, 
  compIndex, 
  setCompIndex,
  formatPrice 
}: { 
  report: ReportData; 
  compIndex: number;
  setCompIndex: (n: number) => void;
  formatPrice: (n: number) => string;
}) {
  const comp = report.comparables[compIndex];
  
  if (!report.comparables.length) {
    return (
      <div className="p-4 text-center text-gray-500">
        No comparable sales found
      </div>
    );
  }

  return (
    <div className="p-4">
      {/* Navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setCompIndex(Math.max(0, compIndex - 1))}
          disabled={compIndex === 0}
          className="p-2 rounded-full bg-white shadow disabled:opacity-30"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <span className="text-sm text-gray-600">
          {compIndex + 1} of {report.comparables.length} Comparables
        </span>
        <button
          onClick={() => setCompIndex(Math.min(report.comparables.length - 1, compIndex + 1))}
          disabled={compIndex === report.comparables.length - 1}
          className="p-2 rounded-full bg-white shadow disabled:opacity-30"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Comp Card */}
      <motion.div
        key={compIndex}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-white overflow-hidden rounded-[var(--radius)] border border-[#ECECE8]"
      >
        {/* Photo */}
        <div className="h-48 relative" style={{ background: 'var(--tint)' }}>
          {comp.photo_url ? (
            <img 
              src={comp.photo_url} 
              alt={comp.address}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 flex flex-col justify-end p-3">
              <span style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 28, lineHeight: 1, color: 'var(--primary-ink)' } as React.CSSProperties}>
                {comp.distance_miles != null && comp.distance_miles > 0 ? `${comp.distance_miles.toFixed(1)} mi` : comp.city}
              </span>
              <span style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 4, color: '#5E636B' }}>
                {comp.distance_miles != null && comp.distance_miles > 0 ? 'From your home · no photo on file' : 'No photo on file'}
              </span>
            </div>
          )}
          <div className="absolute top-2.5 left-2.5 px-2 py-1 bg-white rounded text-sm font-bold" style={{ color: '#14161A' }}>
            {formatPrice(comp.sold_price)}
          </div>
        </div>

        {/* Details */}
        <div className="p-4">
          <p className="font-semibold text-gray-900">{comp.address}</p>
          <p className="text-gray-600 text-sm mb-3">{comp.city}, {report.property.state}</p>
          
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.bedrooms ?? '—'}</p>
              <p className="text-xs text-gray-500">Beds</p>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.bathrooms ?? '—'}</p>
              <p className="text-xs text-gray-500">Baths</p>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.sqft != null ? comp.sqft.toLocaleString() : '—'}</p>
              <p className="text-xs text-gray-500">Sqft</p>
            </div>
          </div>

          <div className="flex justify-between text-sm">
            <span className="text-gray-600">
              <Calendar className="w-4 h-4 inline mr-1" />
              {comp.sold_date ? `Sold ${comp.sold_date}` : comp.days_ago ? `Sold ${comp.days_ago} days ago` : 'Sold'}
            </span>
            <span className="text-gray-600">
              <MapPin className="w-4 h-4 inline mr-1" />
              {comp.distance_miles != null && comp.distance_miles > 0 ? `${comp.distance_miles.toFixed(1)} mi away` : '—'}
            </span>
          </div>

          <div className="mt-3 pt-3 border-t">
            <p className="text-center font-semibold" style={{ color: 'var(--primary-ink)' }}>
              {comp.price_per_sqft != null && comp.price_per_sqft > 0 ? `$${comp.price_per_sqft}/sqft` : '—'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Dots */}
      <div className="flex justify-center gap-1.5 mt-4">
        {report.comparables.map((_, i) => (
          <button
            key={i}
            onClick={() => setCompIndex(i)}
            className="w-2 h-2 rounded-full transition-colors"
            style={{ background: i === compIndex ? 'var(--primary)' : '#D9DADF' }}
          />
        ))}
      </div>
    </div>
  );
}


function MarketTab({ report, formatPrice }: { report: ReportData; formatPrice: (n: number) => string }) {
  const stats = report.market_stats;

  return (
    <div className="p-4 space-y-4">
      <div className="bg-white p-4 rounded-[var(--radius)] border border-[#ECECE8]">
        <h2 className="font-semibold text-gray-900 mb-4">Market Statistics</h2>
        
        <div className="space-y-4">
          <MarketStatRow 
            label="Median Sale Price"
            value={stats.median_price ? formatPrice(stats.median_price) : '—'}
          />
          <MarketStatRow 
            label="Median Price per Sqft"
            value={stats.median_price_per_sqft ? `$${stats.median_price_per_sqft}` : '—'}
          />
          <MarketStatRow 
            label="Avg. Days on Market"
            value={stats.avg_days_on_market ? `${stats.avg_days_on_market} days` : '—'}
          />
          <MarketStatRow 
            label={homesSoldLabel(stats)}
            value={stats.homes_sold ? stats.homes_sold.toString() : '—'}
          />
        </div>
      </div>

      <div className="p-4" style={{ background: '#F6F6F3', border: '1px solid #ECECE8', borderRadius: 'var(--radius)' }}>
        <p className="text-sm m-0" style={{ color: '#5E636B', lineHeight: 1.5 }}>
          {compsSentence(stats)}
        </p>
      </div>
    </div>
  );
}


function AgentTab({ 
  report, 
  onContactClick,
  onDownloadPdf,
  pdfLoading
}: { 
  report: ReportData;
  onContactClick: (type: string) => void;
  onDownloadPdf: () => void;
  pdfLoading: boolean;
}) {
  return (
    <div className="p-4 space-y-4">
      {/* Agent Card */}
      <div className="bg-white p-6 text-center rounded-[var(--radius)] border border-[#ECECE8]">
        {report.agent.photo_url ? (
          <img 
            src={report.agent.photo_url} 
            alt={report.agent.name}
            className="w-24 h-24 rounded-full mx-auto mb-4 object-cover"
          />
        ) : (
          <div className="w-24 h-24 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ background: 'var(--tint)', color: 'var(--primary-ink)' }}>
            <User className="w-12 h-12" />
          </div>
        )}
        
        <h2 className="text-xl font-semibold text-gray-900">{report.agent.name}</h2>
        {report.agent.company_name && (
          <p className="text-gray-600">{report.agent.company_name}</p>
        )}
        {report.agent.license_number && (
          <p className="text-sm text-gray-500">DRE# {report.agent.license_number}</p>
        )}
      </div>

      {/* Contact Buttons */}
      <div className="space-y-3">
        {report.agent.phone && (
          <a
            href={`tel:${report.agent.phone.replace(/[\s().-]/g, '')}`}
            onClick={() => onContactClick('call')}
            className="flex items-center justify-center gap-3 w-full py-4 font-semibold transition"
            style={{ backgroundColor: 'var(--primary)', color: 'var(--on-primary)', borderRadius: 'var(--radius)' }}
          >
            <Phone className="w-5 h-5" />
            Call {report.agent.name.split(' ')[0]}
          </a>
        )}
        
        {report.agent.phone && (
          <a
            href={`sms:${report.agent.phone.replace(/[\s().-]/g, '')}`}
            onClick={() => onContactClick('text')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border-2 font-semibold transition"
            style={{ borderColor: 'var(--primary-ink)', color: 'var(--primary-ink)', borderRadius: 'var(--radius)' }}
          >
            <MessageSquare className="w-5 h-5" />
            Send Text
          </a>
        )}
        
        {report.agent.email && (
          <a
            href={`mailto:${report.agent.email}`}
            onClick={() => onContactClick('email')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border border-gray-300 text-gray-700 rounded-[var(--radius)] font-medium hover:bg-gray-50 transition"
          >
            <Mail className="w-5 h-5" />
            Send Email
          </a>
        )}
      </div>

      {/* Download PDF */}
      <div className="pt-4 border-t">
        <button
          onClick={onDownloadPdf}
          disabled={pdfLoading}
          className="flex items-center justify-center gap-2 w-full py-3 text-gray-600 hover:text-gray-900 transition"
        >
          {pdfLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Download className="w-5 h-5" />
          )}
          {pdfLoading ? 'Generating PDF...' : 'Download Full PDF Report'}
        </button>
      </div>
    </div>
  );
}


// =============================================
// HELPER COMPONENTS
// =============================================

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="bg-white p-3.5 flex flex-col gap-1 rounded-[var(--radius)] border border-[#ECECE8]">
      <p className="m-0" style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 24, lineHeight: 1, letterSpacing: 'var(--display-tracking)' } as React.CSSProperties}>{value}</p>
      <p className="m-0" style={{ fontSize: 11.5, color: '#5E636B' }}>{label}</p>
    </div>
  );
}

function MarketStatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold text-gray-900">{value}</span>
    </div>
  );
}

