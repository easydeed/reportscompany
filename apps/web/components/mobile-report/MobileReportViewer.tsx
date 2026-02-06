'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, Building2, TrendingUp, BarChart3, User,
  Phone, MessageSquare, Mail, Download, Share2,
  ChevronLeft, ChevronRight, MapPin, Calendar,
  Bed, Bath, Square, Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ReportData {
  id: string;
  property: {
    address: string;
    city: string;
    state: string;
    zip: string;
    owner_name?: string;
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
    days_ago: number;
    bedrooms: number;
    bathrooms: number;
    sqft: number;
    price_per_sqft: number;
    distance_miles: number;
    photo_url?: string;
  }>;
  value_estimate: {
    low: number;
    mid: number;
    high: number;
    confidence: string;
  };
  market_stats: {
    median_price?: number;
    avg_price_per_sqft?: number;
    avg_days_on_market?: number;
    total_sold_last_6mo?: number;
  };
  agent: {
    name: string;
    phone?: string;
    email?: string;
    photo_url?: string;
    company_name?: string;
    license_number?: string;
  };
  has_pdf: boolean;
}

interface Props {
  report: ReportData;
  reportId: string;
}

type TabId = 'overview' | 'details' | 'comps' | 'market' | 'agent';

const tabs: { id: TabId; label: string; icon: any }[] = [
  { id: 'overview', label: 'Overview', icon: Home },
  { id: 'details', label: 'Details', icon: Building2 },
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
          const check = await fetch(`/api/proxy/v1/r/${reportId}/pdf/status`);
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

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex-1 min-w-0">
          <h1 className="font-semibold text-gray-900 truncate">
            {report.property.address}
          </h1>
          <p className="text-sm text-gray-500">
            {report.property.city}, {report.property.state}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={handleShare}>
          <Share2 className="w-5 h-5" />
        </Button>
      </header>

      {/* Tab Content */}
      <main className="flex-1 overflow-y-auto pb-20">
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
            {activeTab === 'details' && (
              <DetailsTab report={report} />
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
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-2 py-2 flex justify-around z-50">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col items-center px-3 py-1 rounded-lg transition-colors ${
                isActive 
                  ? 'text-indigo-600 bg-indigo-50' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs mt-0.5">{tab.label}</span>
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
      {/* Hero Card */}
      <div className="bg-gradient-to-br from-violet-600 to-indigo-700 rounded-2xl p-6 text-white">
        <p className="text-violet-200 text-sm mb-1">Estimated Value Range</p>
        <p className="text-3xl font-bold mb-2">
          {formatPrice(report.value_estimate.low)} - {formatPrice(report.value_estimate.high)}
        </p>
        <p className="text-violet-200 text-sm">
          Most likely: {formatPrice(report.value_estimate.mid)}
        </p>
        <div className="mt-4 flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
            report.value_estimate.confidence === 'high' 
              ? 'bg-green-500/20 text-green-100'
              : report.value_estimate.confidence === 'medium'
              ? 'bg-yellow-500/20 text-yellow-100'
              : 'bg-red-500/20 text-red-100'
          }`}>
            {report.value_estimate.confidence} confidence
          </span>
          <span className="text-violet-200 text-xs">
            Based on {report.comparables.length} comparable sales
          </span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard 
          icon={<Bed className="w-5 h-5" />}
          label="Beds"
          value={report.property.bedrooms || '--'}
        />
        <StatCard 
          icon={<Bath className="w-5 h-5" />}
          label="Baths"
          value={report.property.bathrooms || '--'}
        />
        <StatCard 
          icon={<Square className="w-5 h-5" />}
          label="Sqft"
          value={report.property.sqft?.toLocaleString() || '--'}
        />
      </div>

      {/* Address Card */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
            <MapPin className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{report.property.address}</p>
            <p className="text-gray-600">
              {report.property.city}, {report.property.state} {report.property.zip}
            </p>
            {report.property.owner_name && (
              <p className="text-sm text-gray-500 mt-1">
                Owner: {report.property.owner_name}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Agent Preview */}
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-3">
          {report.agent.photo_url ? (
            <img 
              src={report.agent.photo_url} 
              alt={report.agent.name}
              className="w-12 h-12 rounded-full object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="w-6 h-6 text-gray-500" />
            </div>
          )}
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{report.agent.name}</p>
            <p className="text-sm text-gray-600">{report.agent.company_name}</p>
          </div>
          {report.agent.phone && (
            <a 
              href={`tel:${report.agent.phone}`}
              className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center"
            >
              <Phone className="w-5 h-5 text-indigo-600" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}


function DetailsTab({ report }: { report: ReportData }) {
  const details = [
    { label: 'Address', value: report.property.address },
    { label: 'City', value: report.property.city },
    { label: 'State', value: report.property.state },
    { label: 'ZIP', value: report.property.zip },
    { label: 'Owner', value: report.property.owner_name || '--' },
    { label: 'Bedrooms', value: report.property.bedrooms || '--' },
    { label: 'Bathrooms', value: report.property.bathrooms || '--' },
    { label: 'Square Feet', value: report.property.sqft?.toLocaleString() || '--' },
    { label: 'Lot Size', value: report.property.lot_size ? `${report.property.lot_size.toLocaleString()} sqft` : '--' },
    { label: 'Year Built', value: report.property.year_built || '--' },
  ];

  return (
    <div className="p-4">
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h2 className="font-semibold text-gray-900">Property Details</h2>
        </div>
        <div className="divide-y">
          {details.map((item, i) => (
            <div key={i} className="px-4 py-3 flex justify-between">
              <span className="text-gray-600">{item.label}</span>
              <span className="font-medium text-gray-900">{item.value}</span>
            </div>
          ))}
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
        className="bg-white rounded-2xl shadow-sm overflow-hidden"
      >
        {/* Photo */}
        <div className="h-48 bg-gradient-to-br from-gray-200 to-gray-300 relative">
          {comp.photo_url ? (
            <img 
              src={comp.photo_url} 
              alt={comp.address}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <Home className="w-12 h-12 text-gray-400" />
            </div>
          )}
          <div className="absolute top-3 right-3 px-2 py-1 bg-black/70 rounded text-white text-sm font-medium">
            {formatPrice(comp.sold_price)}
          </div>
        </div>

        {/* Details */}
        <div className="p-4">
          <p className="font-semibold text-gray-900">{comp.address}</p>
          <p className="text-gray-600 text-sm mb-3">{comp.city}, {report.property.state}</p>
          
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.bedrooms}</p>
              <p className="text-xs text-gray-500">Beds</p>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.bathrooms}</p>
              <p className="text-xs text-gray-500">Baths</p>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded">
              <p className="text-lg font-semibold">{comp.sqft.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Sqft</p>
            </div>
          </div>

          <div className="flex justify-between text-sm">
            <span className="text-gray-600">
              <Calendar className="w-4 h-4 inline mr-1" />
              Sold {comp.days_ago} days ago
            </span>
            <span className="text-gray-600">
              <MapPin className="w-4 h-4 inline mr-1" />
              {comp.distance_miles.toFixed(1)} mi away
            </span>
          </div>

          <div className="mt-3 pt-3 border-t">
            <p className="text-center text-indigo-600 font-semibold">
              ${comp.price_per_sqft}/sqft
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
            className={`w-2 h-2 rounded-full transition-colors ${
              i === compIndex ? 'bg-indigo-600' : 'bg-gray-300'
            }`}
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
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <h2 className="font-semibold text-gray-900 mb-4">Market Statistics</h2>
        
        <div className="space-y-4">
          <MarketStatRow 
            label="Median Sale Price"
            value={stats.median_price ? formatPrice(stats.median_price) : '--'}
          />
          <MarketStatRow 
            label="Avg. Price per Sqft"
            value={stats.avg_price_per_sqft ? `$${stats.avg_price_per_sqft}` : '--'}
          />
          <MarketStatRow 
            label="Avg. Days on Market"
            value={stats.avg_days_on_market ? `${stats.avg_days_on_market} days` : '--'}
          />
          <MarketStatRow 
            label="Homes Sold (6 mo)"
            value={stats.total_sold_last_6mo?.toString() || '--'}
          />
        </div>
      </div>

      <div className="bg-indigo-50 rounded-xl p-4">
        <p className="text-sm text-violet-800">
          Based on {report.comparables.length} comparable sales within 2 miles 
          of your property in the last 12 months.
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
      <div className="bg-white rounded-xl p-6 shadow-sm text-center">
        {report.agent.photo_url ? (
          <img 
            src={report.agent.photo_url} 
            alt={report.agent.name}
            className="w-24 h-24 rounded-full mx-auto mb-4 object-cover border-4 border-violet-100"
          />
        ) : (
          <div className="w-24 h-24 rounded-full mx-auto mb-4 bg-indigo-100 flex items-center justify-center">
            <User className="w-12 h-12 text-violet-400" />
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
            href={`tel:${report.agent.phone}`}
            onClick={() => onContactClick('call')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition"
          >
            <Phone className="w-5 h-5" />
            Call {report.agent.name.split(' ')[0]}
          </a>
        )}
        
        {report.agent.phone && (
          <a
            href={`sms:${report.agent.phone}`}
            onClick={() => onContactClick('text')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border-2 border-violet-600 text-indigo-600 rounded-xl font-semibold hover:bg-indigo-50 transition"
          >
            <MessageSquare className="w-5 h-5" />
            Send Text
          </a>
        )}
        
        {report.agent.email && (
          <a
            href={`mailto:${report.agent.email}`}
            onClick={() => onContactClick('email')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition"
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
    <div className="bg-white rounded-xl p-3 shadow-sm text-center">
      <div className="text-indigo-600 mb-1 flex justify-center">{icon}</div>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
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

