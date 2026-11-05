import { Metadata } from "next";
import { notFound } from "next/navigation";
import { Barlow, Barlow_Condensed, Cormorant_Garamond, Geist, Manrope } from "next/font/google";
import { themeName } from "@/lib/themes.generated";
import LeadCaptureForm from "./lead-capture-form";

type Props = {
  params: Promise<{ code: string }>;
};

// Theme faces, as the PDF entry files set them
// (apps/worker/src/worker/templates/property/<theme>/<theme>_report.jinja2).
// Self-hosted through next/font; only the theme in use is painted.
const barlowCondensed = Barlow_Condensed({ subsets: ["latin"], weight: ["600", "700"], display: "swap" });
const barlow = Barlow({ subsets: ["latin"], weight: ["400", "500", "600", "700"], display: "swap" });
const cormorant = Cormorant_Garamond({ subsets: ["latin"], weight: ["500", "600"], display: "swap" });
const geist = Geist({ subsets: ["latin"], weight: ["400", "500", "600", "700"], display: "swap" });
const manrope = Manrope({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], display: "swap" });

type ThemeFaces = { display: string; body: string; weight: number; tracking: string; kase: string; radius: string };
const THEME_FACES: Record<string, ThemeFaces> = {
  atlas: { display: `${barlowCondensed.style.fontFamily}, 'Arial Narrow', sans-serif`, body: `${barlow.style.fontFamily}, system-ui, sans-serif`, weight: 700, tracking: "0", kase: "uppercase", radius: "4px" },
  linen: { display: `${cormorant.style.fontFamily}, Georgia, 'Times New Roman', serif`, body: `${geist.style.fontFamily}, system-ui, sans-serif`, weight: 500, tracking: "-0.01em", kase: "none", radius: "0px" },
  harbor: { display: `${manrope.style.fontFamily}, system-ui, sans-serif`, body: `${manrope.style.fontFamily}, system-ui, sans-serif`, weight: 800, tracking: "-0.035em", kase: "none", radius: "14px" },
};

// The derive_theme tokens (apps/worker/src/worker/themes.py), read from the
// response. Until the API carries them the page renders on the one fixed dark
// neutral the PDF uses — readable everywhere, and visibly unbranded so nobody
// mistakes it for done.
type ThemeTokens = { primary: string; primary_dark: string; primary_ink: string; on_primary: string; tint: string; primary_on_dark: string; display_ink: string };
const NEUTRAL_TOKENS: ThemeTokens = { primary: "#0f172a", primary_dark: "#0c1221", primary_ink: "#0f172a", on_primary: "#ffffff", tint: "#f1f2f4", primary_on_dark: "#ffffff", display_ink: "#ffffff" };

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
  theme_tokens?: ThemeTokens | null;
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
  | { status: "inactive"; message: string; theme?: number | null; theme_tokens?: ThemeTokens | null }
  | { status: "expired"; message: string; theme?: number | null; theme_tokens?: ThemeTokens | null }
  | { status: "requires_code"; theme?: number | null; theme_tokens?: ThemeTokens | null }
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
      const theme = data.theme ?? null;
      const theme_tokens = data.theme_tokens ?? null;
      if (message.includes("expired")) {
        return { status: "expired", message, theme, theme_tokens };
      }
      return { status: "inactive", message, theme, theme_tokens };
    }
    
    if (!res.ok) {
      console.error(`[Property Page] API error: ${res.status}`);
      const data = await res.json().catch(() => ({}));
      return { status: "error", message: data.detail || "Something went wrong" };
    }
    
    const data = await res.json();
    
    // Check if access code is required
    if (data.requires_access_code) {
      return { status: "requires_code", theme: data.theme ?? null, theme_tokens: data.theme_tokens ?? null };
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
      title: "Property",
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
  icon,
  theme,
  tokens,
}: { 
  title: string; 
  message: string; 
  icon: "expired" | "inactive" | "error" | "locked";
  theme?: number | null;
  tokens?: ThemeTokens | null;
}) {
  // Not-found and error have no account to theme from; expired/inactive have none until the 410 body
  // carries them. Those render on NEUTRAL_TOKENS and the default faces, as the page does when tokens are missing.
  const t: ThemeTokens = tokens ?? NEUTRAL_TOKENS;
  const faces: ThemeFaces = THEME_FACES[themeName(theme)];
  const themeVars = {
    "--primary": t.primary,
    "--primary-ink": t.primary_ink,
    "--display": faces.display,
    "--body-face": faces.body,
    "--display-weight": faces.weight,
    "--display-tracking": faces.tracking,
    "--display-case": faces.kase,
    "--radius": faces.radius,
  } as React.CSSProperties;
  const iconPath = {
    expired: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
    inactive: "M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636",
    error: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
    locked: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z",
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ ...themeVars, background: "#F6F6F3", fontFamily: "var(--body-face)", color: "#14161A" }}>
      <div className="bg-white max-w-md w-full overflow-hidden" style={{ border: "1px solid #E4E4E0", borderRadius: "var(--radius)" }}>
        <div style={{ height: 8, background: "var(--primary)" }} />
        <div className="p-8 text-center flex flex-col items-center gap-3">
          <svg className="w-14 h-14 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: "var(--primary-ink)" }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={iconPath[icon]} />
          </svg>
          <h1 className="m-0" style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", fontSize: 30, lineHeight: 1.05, letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)", textWrap: "balance" } as unknown as React.CSSProperties}>{title}</h1>
          <p className="m-0" style={{ fontSize: 15, lineHeight: 1.5, color: "#5E636B", textWrap: "pretty" } as React.CSSProperties}>{message}</p>
        </div>
        <div className="mx-8 pt-3.5 pb-6 text-center" style={{ borderTop: "1px solid #E4E4E0", fontSize: 11.5, color: "#5E636B" }}>
          Powered by <span style={{ fontWeight: 700, color: "#14161A" }}>TrendyReports</span>
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
        theme={result.theme}
        tokens={result.theme_tokens}
      />
    );
  }
  
  if (result.status === "expired") {
    return (
      <StatusPage 
        icon="expired"
        title="Page Expired"
        message={result.message}
        theme={result.theme}
        tokens={result.theme_tokens}
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
        theme={result.theme}
        tokens={result.theme_tokens}
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
  const tokens: ThemeTokens = data.theme_tokens ?? NEUTRAL_TOKENS;
  const faces: ThemeFaces = THEME_FACES[themeName(data.theme)];
  const onPrimaryRule = tokens.on_primary.toLowerCase() === "#ffffff" ? "rgba(255,255,255,0.3)" : "rgba(20,21,26,0.25)";
  const themeVars = {
    "--primary": tokens.primary,
    "--primary-ink": tokens.primary_ink,
    "--on-primary": tokens.on_primary,
    "--tint": tokens.tint,
    "--display-ink": tokens.display_ink,
    "--on-primary-rule": onPrimaryRule,
    "--display": faces.display,
    "--body-face": faces.body,
    "--display-weight": faces.weight,
    "--display-tracking": faces.tracking,
    "--display-case": faces.kase,
    "--radius": faces.radius,
  } as React.CSSProperties;
  
  // Format numbers for display
  const formatNumber = (num: number | null) => {
    if (num === null) return null;
    return num.toLocaleString();
  };
  
  return (
    <div className="min-h-screen" style={{ ...themeVars, background: "#F6F6F3", fontFamily: "var(--body-face)", color: "#14161A", fontVariantNumeric: "lining-nums" }}>
      {/* Masthead — the PDF cover band: brand fill, on_primary text, no gradient */}
      <div
        className="relative"
        style={{ background: "var(--primary)", color: "var(--on-primary)" }}
      >
        <div className="max-w-[880px] mx-auto px-5 pt-6 pb-[22px] md:px-10 md:pt-9 md:pb-8 flex flex-col gap-[22px]">
          <div className="flex items-center justify-between gap-3">
            <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 600 }}>Property report</span>
            {data.company_logo_url ? (
              <img
                src={data.company_logo_url}
                alt={data.company_name || "Company"}
                className="h-10 max-w-[200px] w-auto object-contain"
              />
            ) : (
              data.company_name && <span style={{ fontSize: 16, fontWeight: 700, letterSpacing: "-0.01em" }}>{data.company_name}</span>
            )}
          </div>
          <div className="flex flex-col gap-1">
            <h1 className="m-0 text-[36px] md:text-[56px]" style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", lineHeight: 1.1, letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)", color: "var(--display-ink)", textWrap: "balance" } as unknown as React.CSSProperties}>
              {data.property_address}
            </h1>
            <p className="m-0" style={{ fontSize: 16, fontWeight: 500 }}>
              {data.property_city}, {data.property_state} {data.property_zip}
            </p>
          </div>
          <div className="grid grid-cols-4 gap-2 pt-3.5" style={{ borderTop: "1px solid var(--on-primary-rule)" }}>
            {([["Beds", data.bedrooms], ["Baths", data.bathrooms], ["Sq ft", formatNumber(data.sqft)], ["Year built", data.year_built]] as [string, string | number | null][]).map(([label, value]) => (
              <div key={label} className="flex flex-col gap-[3px]">
                <span style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", fontSize: 26, lineHeight: 1, letterSpacing: "var(--display-tracking)", color: "var(--display-ink)" } as React.CSSProperties}>{value ?? "—"}</span>
                <span style={{ fontSize: 11, fontWeight: 500 }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Body — the white sheet under the band; form first on a phone */}
      <div className="max-w-[880px] mx-auto bg-white">
        <div>
          <div className="grid md:grid-cols-2 gap-0">
            
            {/* Agent panel — the PDF's page-6 panel: brand fill, on_primary text, white phone pill in primary_ink */}
            <div className="order-2 md:order-1 p-5 md:p-10 flex flex-col gap-4" style={{ background: "#F6F6F3" }}>
              <div className="flex flex-col gap-4 p-5" style={{ background: "var(--primary)", color: "var(--on-primary)", borderRadius: "var(--radius)" }}>
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full flex-none overflow-hidden flex items-center justify-center bg-white" style={{ color: "var(--primary-ink)", fontFamily: "var(--display)", fontWeight: "var(--display-weight)", fontSize: 24 } as React.CSSProperties}>
                    {data.agent_photo_url ? (
                      <img src={data.agent_photo_url} alt={data.agent_name || "Agent"} className="w-full h-full object-cover" />
                    ) : (
                      data.agent_name ? data.agent_name.charAt(0).toUpperCase() : "A"
                    )}
                  </div>
                  <div className="flex flex-col gap-1 min-w-0">
                    {data.agent_name && (
                      <h2 className="m-0" style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", fontSize: 24, lineHeight: 1, letterSpacing: "var(--display-tracking)" } as React.CSSProperties}>{data.agent_name}</h2>
                    )}
                    {data.company_name && (
                      <p className="m-0" style={{ fontSize: 13 }}>{data.company_name}</p>
                    )}
                  </div>
                </div>
                {(data.agent_phone || data.agent_email) && (
                  <div className="flex flex-col gap-2 text-center">
                    {data.agent_phone && (
                      <a
                        href={`tel:${data.agent_phone.replace(/[\s().-]/g, "")}`}
                        className="block bg-white"
                        style={{ color: "var(--primary-ink)", fontSize: 15, fontWeight: 700, padding: "13px 18px", borderRadius: "var(--radius)", textDecoration: "none" }}
                      >
                        {data.agent_phone}
                      </a>
                    )}
                    {data.agent_email && (
                      <a href={`mailto:${data.agent_email}`} style={{ color: "inherit", fontSize: 13, textDecoration: "none" }}>
                        {data.agent_email}
                      </a>
                    )}
                  </div>
                )}
              </div>
              {data.website_url && (
                <a
                  href={data.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm hover:underline"
                  style={{ color: "var(--primary-ink)" }}
                >
                  Visit website
                </a>
              )}
            </div>
            
            {/* Lead form — first on a phone */}
            <div className="order-1 md:order-2 p-5 md:p-10 bg-white">
              {/* Phone only: whom the visitor is writing to, one line — the full agent panel follows the form */}
              {data.agent_name && (
                <div className="md:hidden flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5 mb-5 pb-4" style={{ borderBottom: "1px solid #E4E4E0", fontSize: 13, color: "#5E636B" }}>
                  <span>
                    <span style={{ fontWeight: 700, color: "#14161A" }}>{data.agent_name}</span>
                    {data.company_name && ` · ${data.company_name}`}
                  </span>
                  {data.agent_phone && (
                    <a href={`tel:${data.agent_phone.replace(/[\s().-]/g, "")}`} style={{ color: "var(--primary-ink)", fontWeight: 600, textDecoration: "none", whiteSpace: "nowrap" }}>{data.agent_phone}</a>
                  )}
                </div>
              )}
              <span className="block mb-2" style={{ fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--primary-ink)", fontWeight: 600 }}>
                About this home
              </span>
              <h3 className="m-0 mb-2" style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", fontSize: 30, lineHeight: 1, letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)" } as unknown as React.CSSProperties}>
                Interested in this property?
              </h3>
              <p className="text-sm mb-6" style={{ color: "#5E636B" }}>
                Fill out the form below and {data.agent_name || "the agent"} will get back to you shortly.
              </p>
              
              <LeadCaptureForm 
                shortCode={data.short_code}
                agentName={data.agent_name}
              />
            </div>
            
          </div>
        </div>
        
        {/* Footer — the PDF's page foot */}
        <div className="mx-5 md:mx-10 pt-3.5 pb-6 flex flex-wrap justify-between items-center gap-3" style={{ borderTop: "1px solid #E4E4E0", fontSize: 11.5, color: "#5E636B" }}>
          <span>
            {data.agent_name && <span style={{ fontWeight: 700, color: "#14161A" }}>{data.agent_name}</span>}
            {data.company_name && ` · ${data.company_name}`}
            {data.agent_phone && ` · ${data.agent_phone}`}
          </span>
          <span>Powered by TrendyReports</span>
        </div>
      </div>
    </div>
  );
}

