import { Metadata } from "next";
import { notFound } from "next/navigation";
import LeadCaptureForm from "./lead-capture-form";

type Props = {
  params: Promise<{ code: string }>;
};

// Types for property report data
interface PropertyReportData {
  property_address: string;
  property_city: string;
  property_state: string;
  property_zip: string;
  property_type: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  sqft: number | null;
  year_built: number | null;
  report_type: string;
  theme: number;
  accent_color: string;
  short_code: string;
  agent_name: string | null;
  agent_photo_url: string | null;
  company_name: string | null;
  company_logo_url: string | null;
  agent_phone: string | null;
  agent_email: string | null;
  website_url: string | null;
  // Landing page controls
  is_active: boolean;
  expires_at: string | null;
  requires_access_code: boolean;
}

type FetchResult = 
  | { status: "success"; data: PropertyReportData }
  | { status: "not_found" }
  | { status: "inactive"; message: string }
  | { status: "expired"; message: string }
  | { status: "requires_code" }
  | { status: "error"; message: string };

async function fetchPropertyReport(code: string): Promise<FetchResult> {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  
  if (!base) {
    console.error("[Property Page] NEXT_PUBLIC_API_BASE not set");
    return { status: "error", message: "Configuration error" };
  }
  
  const url = `${base}/v1/property/public/${code}`;
  
  try {
    const res = await fetch(url, {
      cache: "no-store",
      headers: {
        "Accept": "application/json",
      },
    });
    
    if (res.status === 404) {
      return { status: "not_found" };
    }
    
    if (res.status === 410) {
      // Gone - page inactive or expired
      const data = await res.json().catch(() => ({}));
      const message = data.detail || "This page is no longer available";
      if (message.includes("expired")) {
        return { status: "expired", message };
      }
      return { status: "inactive", message };
    }
    
    if (!res.ok) {
      console.error(`[Property Page] API error: ${res.status}`);
      const data = await res.json().catch(() => ({}));
      return { status: "error", message: data.detail || "Something went wrong" };
    }
    
    const data = await res.json();
    
    // Check if access code is required
    if (data.requires_access_code) {
      return { status: "requires_code" };
    }
    
    return { status: "success", data };
  } catch (error) {
    console.error("[Property Page] Fetch error:", error);
    return { status: "error", message: "Unable to load page" };
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { code } = await params;
  const result = await fetchPropertyReport(code);
  
  if (result.status !== "success") {
    return {
      title: "Property | TrendyReports",
    };
  }
  
  const data = result.data;
  const fullAddress = `${data.property_address}, ${data.property_city}, ${data.property_state} ${data.property_zip}`;
  
  return {
    title: `${fullAddress} | TrendyReports`,
    description: `View property details and connect with ${data.agent_name || "the agent"} about ${fullAddress}`,
  };
}

// Error/Status Page Component
function StatusPage({ 
  title, 
  message, 
  icon 
}: { 
  title: string; 
  message: string; 
  icon: "expired" | "inactive" | "error" | "locked";
}) {
  const iconSvg = {
    expired: (
      <svg className="w-16 h-16 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    inactive: (
      <svg className="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
    error: (
      <svg className="w-16 h-16 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    locked: (
      <svg className="w-16 h-16 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        <div className="flex justify-center mb-6">
          {iconSvg[icon]}
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">{title}</h1>
        <p className="text-slate-600 mb-6">{message}</p>
        <div className="text-sm text-slate-400">
          Powered by <span className="font-medium">TrendyReports</span>
        </div>
      </div>
    </div>
  );
}

export default async function PropertyLandingPage({ params }: Props) {
  const { code } = await params;
  const result = await fetchPropertyReport(code);
  
  // Handle different result statuses
  if (result.status === "not_found") {
    notFound();
  }
  
  if (result.status === "inactive") {
    return (
      <StatusPage 
        icon="inactive"
        title="Page Not Available"
        message={result.message}
      />
    );
  }
  
  if (result.status === "expired") {
    return (
      <StatusPage 
        icon="expired"
        title="Page Expired"
        message={result.message}
      />
    );
  }
  
  if (result.status === "requires_code") {
    // This will be handled by a client component for access code input
    return (
      <StatusPage 
        icon="locked"
        title="Access Code Required"
        message="This property page is protected. Please enter the access code to continue."
      />
    );
  }
  
  if (result.status === "error") {
    return (
      <StatusPage 
        icon="error"
        title="Something Went Wrong"
        message={result.message}
      />
    );
  }
  
  const data = result.data;
  
  const fullAddress = `${data.property_address}, ${data.property_city}, ${data.property_state} ${data.property_zip}`;
  const accentColor = data.accent_color || "#2563eb";
  
  // Format numbers for display
  const formatNumber = (num: number | null) => {
    if (num === null) return null;
    return num.toLocaleString();
  };
  
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <div 
        className="relative h-64 md:h-80"
        style={{
          background: `linear-gradient(135deg, ${accentColor} 0%, ${accentColor}dd 50%, ${accentColor}aa 100%)`,
        }}
      >
        {/* Company Logo */}
        {data.company_logo_url && (
          <div className="absolute top-4 left-4 md:top-6 md:left-6">
            <img 
              src={data.company_logo_url} 
              alt={data.company_name || "Company"} 
              className="h-10 md:h-12 w-auto object-contain filter brightness-0 invert"
            />
          </div>
        )}
        
        {/* Property Address */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white px-4">
          <h1 className="text-2xl md:text-4xl font-bold text-center mb-2 drop-shadow-lg">
            {data.property_address}
          </h1>
          <p className="text-lg md:text-xl opacity-90 drop-shadow">
            {data.property_city}, {data.property_state} {data.property_zip}
          </p>
        </div>
        
        {/* Decorative pattern overlay */}
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
      </div>
      
      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 -mt-12 relative z-10 pb-12">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          
          {/* Property Details */}
          {(data.bedrooms || data.bathrooms || data.sqft || data.year_built) && (
            <div className="border-b border-slate-100 p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                {data.bedrooms && (
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{data.bedrooms}</p>
                    <p className="text-sm text-slate-500">Bedrooms</p>
                  </div>
                )}
                {data.bathrooms && (
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{data.bathrooms}</p>
                    <p className="text-sm text-slate-500">Bathrooms</p>
                  </div>
                )}
                {data.sqft && (
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{formatNumber(data.sqft)}</p>
                    <p className="text-sm text-slate-500">Sq Ft</p>
                  </div>
                )}
                {data.year_built && (
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{data.year_built}</p>
                    <p className="text-sm text-slate-500">Year Built</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Agent Info + Lead Form Grid */}
          <div className="grid md:grid-cols-2 gap-0">
            
            {/* Agent Info */}
            <div className="p-6 md:p-8 bg-slate-50 border-b md:border-b-0 md:border-r border-slate-100">
              <div className="flex items-start gap-4">
                {data.agent_photo_url ? (
                  <img 
                    src={data.agent_photo_url} 
                    alt={data.agent_name || "Agent"} 
                    className="w-20 h-20 rounded-full object-cover shadow-md"
                  />
                ) : (
                  <div 
                    className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-md"
                    style={{ backgroundColor: accentColor }}
                  >
                    {data.agent_name ? data.agent_name.charAt(0).toUpperCase() : "A"}
                  </div>
                )}
                <div className="flex-1">
                  {data.agent_name && (
                    <h2 className="text-xl font-semibold text-slate-900">{data.agent_name}</h2>
                  )}
                  {data.company_name && (
                    <p className="text-slate-600">{data.company_name}</p>
                  )}
                  
                  <div className="mt-3 space-y-1">
                    {data.agent_phone && (
                      <a 
                        href={`tel:${data.agent_phone}`}
                        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        {data.agent_phone}
                      </a>
                    )}
                    {data.agent_email && (
                      <a 
                        href={`mailto:${data.agent_email}`}
                        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        {data.agent_email}
                      </a>
                    )}
                  </div>
                </div>
              </div>
              
              {data.website_url && (
                <a 
                  href={data.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-flex items-center gap-1 text-sm hover:underline"
                  style={{ color: accentColor }}
                >
                  Visit Website
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              )}
            </div>
            
            {/* Lead Capture Form */}
            <div className="p-6 md:p-8">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                Interested in this property?
              </h3>
              <p className="text-slate-600 text-sm mb-6">
                Fill out the form below and {data.agent_name || "the agent"} will get back to you shortly.
              </p>
              
              <LeadCaptureForm 
                shortCode={data.short_code}
                agentName={data.agent_name}
                accentColor={accentColor}
              />
            </div>
            
          </div>
        </div>
        
        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Powered by <span className="font-medium">TrendyReports</span></p>
        </div>
      </div>
    </div>
  );
}

