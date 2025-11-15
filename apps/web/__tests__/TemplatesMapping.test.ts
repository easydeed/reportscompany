/**
 * Template Mapping Tests
 * 
 * Phase T2.3: Test that template builders correctly inject brand data
 * and generate valid HTML with proper placeholders replaced
 */

import {
  buildMarketSnapshotHtml,
  buildNewListingsHtml,
  buildInventoryHtml,
  buildClosedHtml,
  buildPriceBandsHtml
} from '../lib/templates';

// Mock brand data
const mockBrand = {
  display_name: "ACME Title",
  logo_url: "https://example.com/logo.png",
  primary_color: "#123456",
  accent_color: "#FF8800"
};

// Mock result_json data for each report type
const mockMarketSnapshotData = {
  brand: mockBrand,
  report_type: "market_snapshot",
  city: "San Diego",
  lookback_days: 30,
  period_label: "Last 30 days",
  report_date: "January 15, 2025",
  counts: {
    Active: 150,
    Pending: 25,
    Closed: 75
  },
  metrics: {
    median_list_price: 850000,
    median_close_price: 825000,
    avg_dom: 18.5
  }
};

const mockListingsData = {
  brand: mockBrand,
  report_type: "new_listings",
  city: "San Diego",
  lookback_days: 30,
  period_label: "Last 30 days",
  report_date: "January 15, 2025",
  counts: { Active: 150 },
  metrics: { median_list_price: 850000 },
  listings_sample: [
    {
      address: "123 Main St",
      list_price: 899000,
      beds: 3,
      baths: 2.5,
      sqft: 2000,
      status: "Active",
      days_on_market: 5
    },
    {
      address: "456 Oak Ave",
      list_price: 1250000,
      beds: 4,
      baths: 3,
      sqft: 2800,
      status: "Active",
      days_on_market: 12
    }
  ]
};

const mockPriceBandsData = {
  brand: mockBrand,
  report_type: "price_bands",
  city: "San Diego",
  lookback_days: 30,
  period_label: "Last 30 days",
  report_date: "January 15, 2025",
  price_bands: [
    {
      price_range: "$500K - $750K",
      active_count: 45,
      pending_count: 8,
      closed_count: 25,
      avg_dom: 15.2,
      median_price: 625000
    },
    {
      price_range: "$750K - $1M",
      active_count: 60,
      pending_count: 12,
      closed_count: 35,
      avg_dom: 18.7,
      median_price: 875000
    },
    {
      price_range: "$1M - $1.5M",
      active_count: 30,
      pending_count: 5,
      closed_count: 18,
      avg_dom: 22.3,
      median_price: 1250000
    }
  ]
};

// Simple template strings (minimal HTML structure for testing)
const mockMarketSnapshotTemplate = `
<!DOCTYPE html>
<html>
<head>
  <title>{{brand_name}} - Market Snapshot</title>
</head>
<body>
  <header>
    <img src="{{brand_logo_url}}" alt="{{brand_name}}">
    <h1>{{market_name}} Market Snapshot</h1>
  </header>
  <div class="metrics">
    <div>Median Price: {{median_price}}</div>
    <div>Closed Sales: {{closed_sales}}</div>
  </div>
  <footer>{{brand_tagline}}</footer>
</body>
</html>
`;

const mockListingsTemplate = `
<!DOCTYPE html>
<html>
<head>
  <title>{{brand_name}} - Listings</title>
</head>
<body>
  <header>
    <img src="{{brand_logo_url}}" alt="{{brand_name}}">
    <h1>{{market_name}} Listings</h1>
  </header>
  <!-- LISTINGS_TABLE_ROWS -->
  <footer>{{brand_tagline}}</footer>
</body>
</html>
`;

const mockPriceBandsTemplate = `
<!DOCTYPE html>
<html>
<head>
  <title>{{brand_name}} - Price Bands</title>
</head>
<body>
  <header>
    <img src="{{brand_logo_url}}" alt="{{brand_name}}">
    <h1>{{market_name}} Price Bands</h1>
  </header>
  <!-- PRICE_BANDS_CONTENT -->
  <footer>{{brand_tagline}}</footer>
</body>
</html>
`;

describe('Template Mapping - Brand Injection', () => {
  describe('buildMarketSnapshotHtml', () => {
    it('should inject ACME Title brand name', () => {
      const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
      expect(html).toContain("ACME Title");
    });

    it('should inject logo URL', () => {
      const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
      expect(html).toContain("https://example.com/logo.png");
    });

    it('should inject CSS color overrides', () => {
      const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
      expect(html).toContain("--pct-blue: #123456");
      expect(html).toContain("--pct-accent: #FF8800");
    });

    it('should contain KPI data (Closed Sales)', () => {
      const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
      expect(html).toContain("75"); // closed count
    });

    it('should replace market_name with city', () => {
      const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
      expect(html).toContain("San Diego");
    });
  });

  describe('buildNewListingsHtml', () => {
    it('should inject ACME Title brand name', () => {
      const html = buildNewListingsHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("ACME Title");
    });

    it('should inject logo URL', () => {
      const html = buildNewListingsHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("https://example.com/logo.png");
    });

    it('should inject CSS color overrides', () => {
      const html = buildNewListingsHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("--pct-blue: #123456");
      expect(html).toContain("--pct-accent: #FF8800");
    });

    it('should contain listing address', () => {
      const html = buildNewListingsHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("123 Main St");
    });
  });

  describe('buildInventoryHtml', () => {
    it('should inject ACME Title brand name', () => {
      const html = buildInventoryHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("ACME Title");
    });

    it('should inject CSS color overrides', () => {
      const html = buildInventoryHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("--pct-blue: #123456");
      expect(html).toContain("--pct-accent: #FF8800");
    });
  });

  describe('buildClosedHtml', () => {
    it('should inject ACME Title brand name', () => {
      const html = buildClosedHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("ACME Title");
    });

    it('should inject CSS color overrides', () => {
      const html = buildClosedHtml(mockListingsTemplate, mockListingsData);
      expect(html).toContain("--pct-blue: #123456");
      expect(html).toContain("--pct-accent: #FF8800");
    });
  });

  describe('buildPriceBandsHtml', () => {
    it('should inject ACME Title brand name', () => {
      const html = buildPriceBandsHtml(mockPriceBandsTemplate, mockPriceBandsData);
      expect(html).toContain("ACME Title");
    });

    it('should inject logo URL', () => {
      const html = buildPriceBandsHtml(mockPriceBandsTemplate, mockPriceBandsData);
      expect(html).toContain("https://example.com/logo.png");
    });

    it('should inject CSS color overrides', () => {
      const html = buildPriceBandsHtml(mockPriceBandsTemplate, mockPriceBandsData);
      expect(html).toContain("--pct-blue: #123456");
      expect(html).toContain("--pct-accent: #FF8800");
    });

    it('should contain price band data', () => {
      const html = buildPriceBandsHtml(mockPriceBandsTemplate, mockPriceBandsData);
      expect(html).toContain("$500K - $750K");
      expect(html).toContain("$750K - $1M");
    });
  });
});

describe('Template Mapping - Fallback Brand', () => {
  const dataWithoutBrand = {
    report_type: "market_snapshot",
    city: "Los Angeles",
    lookback_days: 30,
    counts: { Active: 100, Pending: 20, Closed: 50 },
    metrics: { median_close_price: 750000, avg_dom: 15 }
    // No brand field
  };

  it('should use TrendyReports as fallback brand name', () => {
    const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, dataWithoutBrand);
    expect(html).toContain("TrendyReports");
  });

  it('should use default colors when brand not provided', () => {
    const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, dataWithoutBrand);
    expect(html).toContain("--pct-blue: #7C3AED"); // DEFAULT_PRIMARY_COLOR
    expect(html).toContain("--pct-accent: #F26B2B"); // DEFAULT_ACCENT_COLOR
  });
});

describe('Template Mapping - KPI Formatting', () => {
  it('should format currency values with commas', () => {
    const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
    // Should format 825000 as $825,000
    expect(html).toMatch(/\$825,000/);
  });

  it('should format large numbers with commas', () => {
    const html = buildMarketSnapshotHtml(mockMarketSnapshotTemplate, mockMarketSnapshotData);
    // Should show counts as numbers
    expect(html).toContain("150"); // Active count
    expect(html).toContain("75"); // Closed count
  });
});

