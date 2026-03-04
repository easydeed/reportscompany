'use client';

import { useState } from 'react';
import { MarketNarrativeLayout } from './layouts/market-narrative';
import { Gallery2x2Layout } from './layouts/gallery-2x2';
import { Gallery3x2Layout } from './layouts/gallery-3x2';
import { SingleStackedLayout } from './layouts/single-stacked';
import { LargeListLayout } from './layouts/large-list';
import { ClosedSalesTableLayout } from './layouts/closed-sales-table';
import { MarketAnalyticsLayout } from './layouts/market-analytics';

const layouts = [
  { id: 'market-narrative', name: 'Market Narrative', description: 'Data-heavy reports with storytelling' },
  { id: 'gallery-2x2', name: 'Gallery 2x2', description: '4 featured properties' },
  { id: 'gallery-3x2', name: 'Gallery 3x2', description: '6 properties compact' },
  { id: 'single-stacked', name: 'Single Stacked', description: 'Magazine-style luxury' },
  { id: 'large-list', name: 'Large List', description: '10+ properties' },
  { id: 'closed-sales', name: 'Closed Sales Table', description: 'Sales data with table' },
  { id: 'market-analytics', name: 'Market Analytics', description: 'Trends & year-over-year' },
];

export default function EmailTemplatesPage() {
  const [activeLayout, setActiveLayout] = useState('market-narrative');

  const renderLayout = () => {
    switch (activeLayout) {
      case 'market-narrative':
        return <MarketNarrativeLayout />;
      case 'gallery-2x2':
        return <Gallery2x2Layout />;
      case 'gallery-3x2':
        return <Gallery3x2Layout />;
      case 'single-stacked':
        return <SingleStackedLayout />;
      case 'large-list':
        return <LargeListLayout />;
      case 'closed-sales':
        return <ClosedSalesTableLayout />;
      case 'market-analytics':
        return <MarketAnalyticsLayout />;
      default:
        return <MarketNarrativeLayout />;
    }
  };

  return (
    <div className="min-h-screen bg-stone-100">
      {/* Header Navigation */}
      <div className="sticky top-0 z-50 bg-white border-b border-stone-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-xl font-semibold text-stone-900 mb-4">Email Template Layouts — Visual Reference</h1>
          <div className="flex flex-wrap gap-2">
            {layouts.map((layout) => (
              <button
                key={layout.id}
                onClick={() => setActiveLayout(layout.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeLayout === layout.id
                    ? 'bg-[#1B365D] text-white'
                    : 'bg-stone-100 text-stone-700 hover:bg-stone-200'
                }`}
              >
                {layout.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Layout Preview */}
      <div className="py-8 px-4">
        <div className="max-w-[640px] mx-auto">
          {/* Email container simulation */}
          <div className="bg-stone-200 p-5 rounded-lg shadow-inner">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              {renderLayout()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
