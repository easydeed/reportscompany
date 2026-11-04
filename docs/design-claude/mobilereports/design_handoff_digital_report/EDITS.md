# Edits — the digital report (/p/[code] and /r/[id])

Cut against `easydeed/reportscompany` **main**, main as read 2026-11-04T18:10Z (tree d70f6df2f744). Three live files, 49 touches, one change each. Apply with `apply_touches.py` (`--check` first); it refuses if any anchor moved. `touches.json` is the source of this document.

Fixed-rule flags are marked **FLAG (rule 6)** in the *why*. Data dependencies (rule 5 — yours, not in this package) are marked **FLAG (rule 5)**; the edits ship with a neutral fallback so they build before those land.


## `apps/web/app/p/[code]/page.tsx`

### P1 — /p — module head

The theme faces and the registry name lookup. Barlow/Barlow Condensed (atlas), Cormorant Garamond/Geist (linen), Manrope (harbor) are what the PDF entry files set; `themeName` is the generated single-source id→name map (D-163).

**Before**

```tsx
import { Metadata } from "next";
import { notFound } from "next/navigation";
import LeadCaptureForm from "./lead-capture-form";

```

**After**

```tsx
import { Metadata } from "next";
import { notFound } from "next/navigation";
import { Barlow, Barlow_Condensed, Cormorant_Garamond, Geist, Manrope } from "next/font/google";
import { themeName } from "@/lib/themes.generated";
import LeadCaptureForm from "./lead-capture-form";

```

### P2 — /p — module head

Theme faces per theme and the token type, module-scope. FLAG (rule 6 — derived inks): tokens are the PDF's derive_theme values; the page never computes a colour. FLAG (rule 5 — data): `theme_tokens` is not on the public response yet; NEUTRAL_TOKENS is the fallback until it is.

**Before**

```tsx
type Props = {
  params: Promise<{ code: string }>;
};

```

**After**

```tsx
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

```

### P3 — /p — response type

The field the tokens arrive on. Optional so the page builds before the API change lands. FLAG (rule 5): the API side — `derive_theme(accent_color)` serialised onto `/v1/property/public/{code}` — is yours; this is only the type.

**Before**

```tsx
  theme: number;
  accent_color: string;
  short_code: string;
```

**After**

```tsx
  theme: number;
  accent_color: string;
  theme_tokens?: ThemeTokens | null;
  short_code: string;
```

### P4 — /p — page setup

Tokens, faces and the CSS custom properties the whole page reads. `accent_color` on a property report IS the PDF's brand colour (property_builder._get_theme_color prefers it) — it is passed to the form unchanged; the form now reads the variables, not the prop.

**Before**

```tsx
  const accentColor = data.accent_color || "#2563eb";

```

**After**

```tsx
  const accentColor = data.accent_color || "#2563eb";
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

```

### P5 — /p — hero

The accent gradient under white text (page.tsx ~218) becomes the PDF cover band: a flat brand fill carrying on_primary. FLAG (rule 6 — text on gradients, brand colour, derived inks). The root takes the theme variables and the body face.

**Before**

```tsx
    <div className="min-h-screen bg-slate-50">
      {/* Hero Section */}
      <div 
        className="relative h-64 md:h-80"
        style={{
          background: `linear-gradient(135deg, ${accentColor} 0%, ${accentColor}dd 50%, ${accentColor}aa 100%)`,
        }}
      >
```

**After**

```tsx
    <div className="min-h-screen" style={{ ...themeVars, background: "#F6F6F3", fontFamily: "var(--body-face)", color: "#14161A", fontVariantNumeric: "lining-nums" }}>
      {/* Masthead — the PDF cover band: brand fill, on_primary text, no gradient */}
      <div
        className="relative"
        style={{ background: "var(--primary)", color: "var(--on-primary)" }}
      >
```

### P6 — /p — hero content

Logo as supplied (no brightness-0 invert — it painted every logo white), report kind + brand on one row, street in the display face at display_ink, city at on_primary, then the four cover stats with dashes for missing values. FLAG (rule 6 — missing-data dashes; text on brand = derived inks). The pattern overlay goes: it was a translucent layer under text.

**Before**

```tsx
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
```

**After**

```tsx
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
            <h1 className="m-0 text-[36px] md:text-[56px]" style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", lineHeight: 1.1, letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)", color: "var(--display-ink)", textWrap: "balance" } as React.CSSProperties}>
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
```

### P7 — /p — body

The floating card becomes the white sheet under the band, 880px like the PDF. The stats block leaves the card (it is on the band now — P6) and its four-condition guard goes with it: a missing value is a dash, not an absent block.

**Before**

```tsx
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
```

**After**

```tsx
      {/* Body — the white sheet under the band; form first on a phone */}
      <div className="max-w-[880px] mx-auto bg-white">
        <div>
          <div className="grid md:grid-cols-2 gap-0">
```

### P8 — /p — agent block

The slate agent card becomes the PDF page-6 agent panel: brand fill, on_primary text, the display face for the name, a white phone pill in primary_ink, tel:/mailto: with the number stripped for dialling. Second on a phone (order-2), left on a desktop. FLAG (rule 6 — derived inks).

**Before**

```tsx
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
```

**After**

```tsx
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
```

### P9 — /p — form heading

The form comes first on a phone (order-1) — it is what the page is for. Its heading takes the page's label voice and the display face; copy unchanged.

**Before**

```tsx
            {/* Lead Capture Form */}
            <div className="p-6 md:p-8">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                Interested in this property?
              </h3>
              <p className="text-slate-600 text-sm mb-6">
```

**After**

```tsx
            {/* Lead form — first on a phone */}
            <div className="order-1 md:order-2 p-5 md:p-10 bg-white">
              <span className="block mb-2" style={{ fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--primary-ink)", fontWeight: 600 }}>
                About this home
              </span>
              <h3 className="m-0 mb-2" style={{ fontFamily: "var(--display)", fontWeight: "var(--display-weight)", fontSize: 30, lineHeight: 1, letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)" } as React.CSSProperties}>
                Interested in this property?
              </h3>
              <p className="text-sm mb-6" style={{ color: "#5E636B" }}>
```

### P10 — /p — footer

"Powered by" becomes the PDF page foot: agent · company · phone on the left, the product on the right, over a hairline.

**Before**

```tsx
        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Powered by <span className="font-medium">TrendyReports</span></p>
        </div>
```

**After**

```tsx
        {/* Footer — the PDF's page foot */}
        <div className="mx-5 md:mx-10 pt-3.5 pb-6 flex flex-wrap justify-between items-center gap-3" style={{ borderTop: "1px solid #E4E4E0", fontSize: 11.5, color: "#5E636B" }}>
          <span>
            {data.agent_name && <span style={{ fontWeight: 700, color: "#14161A" }}>{data.agent_name}</span>}
            {data.company_name && ` · ${data.company_name}`}
            {data.agent_phone && ` · ${data.agent_phone}`}
          </span>
          <span>Powered by TrendyReports</span>
        </div>
```

## `apps/web/app/p/[code]/lead-capture-form.tsx`

### F1 — /p — form success

The 20%-alpha accent disc becomes the tint token; the check stroke is primary_ink. The form sits inside the themed root, so it reads the CSS variables and no prop changes.

**Before**

```tsx
          style={{ backgroundColor: `${accentColor}20` }}
        >
          <svg 
            className="w-8 h-8" 
            fill="none" 
            stroke={accentColor} 
```

**After**

```tsx
          style={{ backgroundColor: "var(--tint)" }}
        >
          <svg 
            className="w-8 h-8" 
            fill="none" 
            stroke="var(--primary-ink)" 
```

### F2 — /p — form labels

Labels in the PDF body colour at weight 600; four of them.

Occurs **4×**; all replaced.

**Before**

```tsx
          className="block text-sm font-medium text-slate-700 mb-1"
```

**After**

```tsx
          className="block text-[13px] font-semibold mb-1.5"
          style={{ color: "#2A2D33" }}
```

### F3 — /p — required marks

The required asterisk in primary_ink rather than red: red is reserved for the error state below.

Occurs **2×**; all replaced.

**Before**

```tsx
<span className="text-red-500">*</span>
```

**After**

```tsx
<span style={{ color: "var(--primary-ink)" }}>*</span>
```

### F4 — /p — optional marks

The (optional) note in the PDF muted grey, weight 400.

Occurs **2×**; all replaced.

**Before**

```tsx
<span className="text-slate-400">(optional)</span>
```

**After**

```tsx
<span className="font-normal" style={{ color: "#5E636B" }}>(optional)</span>
```

### F5 — /p — text inputs

Inputs take the theme corner, the PDF axis-rule border, 15px type and a 48px tap height; focus ring in primary_ink. Three inputs.

Occurs **3×**; all replaced.

**Before**

```tsx
          className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all"
          style={{ 
            "--tw-ring-color": accentColor,
          } as React.CSSProperties}
```

**After**

```tsx
          className="w-full px-4 py-3 border outline-none transition-all focus:ring-2 focus:border-transparent"
          style={{ 
            "--tw-ring-color": "var(--primary-ink)",
            borderColor: "#D9DADF",
            borderRadius: "var(--radius)",
            fontSize: 15,
          } as React.CSSProperties}
```

### F6 — /p — textarea

Same as F5 for the message field.

**Before**

```tsx
          className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:border-transparent outline-none transition-all resize-none"
          style={{ 
            "--tw-ring-color": accentColor,
          } as React.CSSProperties}
```

**After**

```tsx
          className="w-full px-4 py-3 border outline-none transition-all focus:ring-2 focus:border-transparent resize-none"
          style={{ 
            "--tw-ring-color": "var(--primary-ink)",
            borderColor: "#D9DADF",
            borderRadius: "var(--radius)",
            fontSize: 15,
          } as React.CSSProperties}
```

### F7 — /p — consent

Consent becomes required: the `required` attribute and the asterisk are the template half; the handler check in handleSubmit (and the server) is yours. Checkbox at 20px for the thumb, accent-color from the brand.

**Before**

```tsx
          className="mt-1 w-4 h-4 rounded border-slate-300"
          style={{ accentColor }}
          disabled={status === "submitting"}
        />
        <label 
          htmlFor="consent_given" 
          className="text-sm text-slate-600"
        >
          I consent to being contacted about this property and related services.
        </label>
```

**After**

```tsx
          className="mt-0.5 w-5 h-5 rounded border-slate-400"
          style={{ accentColor: "var(--primary)" }}
          required
          disabled={status === "submitting"}
        />
        <label 
          htmlFor="consent_given" 
          className="text-[13px] leading-normal"
          style={{ color: "#2A2D33" }}
        >
          I consent to being contacted about this property and related services. <span style={{ color: "var(--primary-ink)" }}>*</span>
        </label>
```

### F8 — /p — submit

The accent fill under white text becomes the brand fill under on_primary. FLAG (rule 6 — brand colour, derived inks). Theme corner.

**Before**

```tsx
        className="w-full py-3 px-4 text-white font-medium rounded-lg transition-all hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
        style={{ backgroundColor: accentColor }}
```

**After**

```tsx
        className="w-full py-3.5 px-4 font-bold transition-all hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
        style={{ backgroundColor: "var(--primary)", color: "var(--on-primary)", borderRadius: "var(--radius)", fontSize: 15 }}
```

### F9 — /p — form footnote

Footnote in the PDF muted grey.

**Before**

```tsx
      <p className="text-xs text-slate-500 text-center">
```

**After**

```tsx
      <p className="text-xs text-center" style={{ color: "#5E636B" }}>
```

## `apps/web/components/mobile-report/MobileReportViewer.tsx`

### R1 — /r — module head

Same faces and registry lookup as P1/P2, in the client component. FLAG (rule 5 — data): `theme` and `theme_tokens` are not on `/v1/r/{id}/data`; `themeName(undefined)` resolves to the registry default (atlas) and NEUTRAL_TOKENS carries the colour until they are.

**Before**

```tsx
import { Button } from '@/components/ui/button';

```

**After**

```tsx
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

```

### R2 — /r — response type

The two fields the theme arrives on, optional. FLAG (rule 5): the API side is yours — `consumer_reports.theme_id` and `derive_theme(...)` of the colour the consumer PDF is built from.

**Before**

```tsx
  branding?: {
    primary_color: string;
    accent_color: string;
    logo_url?: string;
  };
  has_pdf: boolean;
}
```

**After**

```tsx
  branding?: {
    primary_color: string;
    accent_color: string;
    logo_url?: string;
  };
  theme?: number | null;
  theme_tokens?: ThemeTokens | null;
  has_pdf: boolean;
}
```

### R3 — /r — viewer setup

Tokens, faces and the CSS variables, once, on the root.

**Before**

```tsx
  const formatPrice = (n: number) => `$${n.toLocaleString()}`;

```

**After**

```tsx
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

```

### R4 — /r — root

Page background is the PDF strip; body face and ink from the theme.

**Before**

```tsx
    <div className="min-h-screen bg-gray-50 flex flex-col">
```

**After**

```tsx
    <div className="min-h-screen flex flex-col" style={{ ...themeVars, background: '#F6F6F3', fontFamily: 'var(--body-face)', color: '#14161A', fontVariantNumeric: 'lining-nums' }}>
```

### R5 — /r — header

The header is the report's masthead on a phone: kind label in primary_ink, street in the display face, city line with the ZIP, PDF hairline.

**Before**

```tsx
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex-1 min-w-0">
          <h1 className="font-semibold text-gray-900 truncate">
            {report.property.address}
          </h1>
          <p className="text-sm text-gray-500">
            {report.property.city}, {report.property.state}
          </p>
        </div>
```

**After**

```tsx
      <header className="bg-white px-4 py-3 flex items-center justify-between sticky top-0 z-50" style={{ borderBottom: '1px solid #ECECE8' }}>
        <div className="flex-1 min-w-0 flex flex-col">
          <span style={{ fontSize: 10.5, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--primary-ink)', fontWeight: 600, whiteSpace: 'nowrap' }}>Home value report</span>
          <h1 className="truncate m-0" style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 22, lineHeight: 1.05, letterSpacing: 'var(--display-tracking)', textTransform: 'var(--display-case)' } as React.CSSProperties}>
            {report.property.address}
          </h1>
          <p className="m-0" style={{ fontSize: 12.5, color: '#5E636B' }}>
            {report.property.city}, {report.property.state} {report.property.zip}
          </p>
        </div>
```

### R6 — /r — desktop column

Phone first, desktop second: content holds a 560px column on wide screens instead of stretching to the viewport.

**Before**

```tsx
      <main className="flex-1 overflow-y-auto pb-20">
```

**After**

```tsx
      <main className="flex-1 overflow-y-auto pb-20 w-full max-w-[560px] mx-auto">
```

### R7 — /r — tab bar

The bar holds the same 560px column; PDF hairline instead of the default border.

**Before**

```tsx
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-2 py-2 flex justify-around z-50">
```

**After**

```tsx
      <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[560px] bg-white flex justify-around z-50" style={{ borderTop: '1px solid #ECECE8' }}>
```

### R8 — /r — tab item

Active tab: primary_ink text and a 2px brand bar on top — no 15%-alpha brand wash, which is a tinted surface and a colour nobody chose (REPORT_VIEWER_TINTS l.232). Inactive: PDF muted grey.

**Before**

```tsx
              className={`flex flex-col items-center px-3 py-1 rounded-lg transition-colors ${
                isActive 
                  ? '' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              style={isActive ? { color: report.branding?.primary_color || '#6366f1', backgroundColor: `${report.branding?.primary_color || '#6366f1'}15` } : {}}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs mt-0.5">{tab.label}</span>
```

**After**

```tsx
              className="flex flex-col items-center gap-[3px] px-2.5 pt-2.5 pb-2 min-w-[56px] -mt-px transition-colors"
              style={{ color: isActive ? 'var(--primary-ink)' : '#5E636B', fontWeight: isActive ? 600 : 500, borderTop: `2px solid ${isActive ? 'var(--primary)' : 'transparent'}` }}
            >
              <Icon className="w-5 h-5" />
              <span style={{ fontSize: 11.5 }}>{tab.label}</span>
```

### R9 — /r — overview value box

The brand-to-accent gradient under violet text (l.253) becomes the PDF range panel on the one fixed dark neutral (#0f172a): label in primary_on_dark, the range in the display face, the method line beside it. No "most likely" figure; no confidence pill (a tinted fill behind semantic text). FLAG (rule 6 — estimate panel, text on gradients, derived inks). Reads the fields you are correcting (low/high = comps range).

**Before**

```tsx
      {/* Hero Card */}
      <div className="rounded-2xl p-6 text-white" style={{ background: `linear-gradient(135deg, ${report.branding?.primary_color || '#6366f1'} 0%, ${report.branding?.accent_color || '#8b5cf6'} 100%)` }}>
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
```

**After**

```tsx
      {/* Range panel — the PDF's page-4 panel on the one fixed dark neutral; primary_on_dark is guaranteed against it and nothing else */}
      <div className="p-5 text-white flex flex-col gap-3" style={{ background: '#0f172a', borderRadius: 'var(--radius)' }}>
        <span style={{ fontSize: 10.5, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--primary-on-dark)', fontWeight: 600 }}>
          Range supported by {report.comparables.length} closed sales
        </span>
        <span style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 34, lineHeight: 0.95, letterSpacing: 'var(--display-tracking)', textWrap: 'balance' } as React.CSSProperties}>
          {formatPrice(report.value_estimate.low)} – {formatPrice(report.value_estimate.high)}
        </span>
        <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)' }}>Range of the comparable sales shown.</span>
      </div>
```

### R10 — /r — missing values

A missing value is an em dash, as on the PDF, not two hyphens. Twelve sites across overview, details and market. FLAG (rule 6 — missing-data dashes).

Occurs **12×**; all replaced.

**Before**

```tsx
'--'
```

**After**

```tsx
'—'
```

### R11 — /r — white cards

Cards take the theme corner and the PDF hairline instead of rounded-xl and a shadow. Three cards (address, agent preview, market).

Occurs **3×**; all replaced.

**Before**

```tsx
className="bg-white rounded-xl p-4 shadow-sm"
```

**After**

```tsx
className="bg-white p-4 rounded-[var(--radius)] border border-[#ECECE8]"
```

### R12 — /r — address chip

The indigo MapPin chip goes (REPORT_VIEWER_TINTS l.299–300): an icon chip in a hue that follows no brand.

**Before**

```tsx
          <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
            <MapPin className="w-5 h-5 text-indigo-600" />
          </div>

```

**After**

```tsx
(removed)
```

### R13 — /r — agent preview avatar

Fallback avatar on the tint token with the glyph in primary_ink.

**Before**

```tsx
            <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
              <User className="w-6 h-6 text-gray-500" />
            </div>
```

**After**

```tsx
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'var(--tint)', color: 'var(--primary-ink)' }}>
              <User className="w-6 h-6" />
            </div>
```

### R14 — /r — agent preview phone

The indigo phone chip (l.337–339) becomes a 44px brand-fill button with the glyph in on_primary; the number is stripped for dialling.

**Before**

```tsx
              href={`tel:${report.agent.phone}`}
              className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center"
            >
              <Phone className="w-5 h-5 text-indigo-600" />
```

**After**

```tsx
              href={`tel:${report.agent.phone.replace(/[\s().-]/g, '')}`}
              className="w-11 h-11 rounded-full flex items-center justify-center"
              style={{ background: 'var(--primary)', color: 'var(--on-primary)' }}
            >
              <Phone className="w-5 h-5" />
```

### R15 — /r — comp photo plate

The grey gradient plate becomes the tint plate the PDF uses.

**Before**

```tsx
        <div className="h-48 bg-gradient-to-br from-gray-200 to-gray-300 relative">
```

**After**

```tsx
        <div className="h-48 relative" style={{ background: 'var(--tint)' }}>
```

### R16 — /r — comp missing photo

The PDF missing-photo tile: distance from the subject in the display face (city when distance is unknown), with the note. Replaces a grey house glyph.

**Before**

```tsx
            <div className="absolute inset-0 flex items-center justify-center">
              <Home className="w-12 h-12 text-gray-400" />
            </div>
```

**After**

```tsx
            <div className="absolute inset-0 flex flex-col justify-end p-3">
              <span style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 28, lineHeight: 1, color: 'var(--primary-ink)' } as React.CSSProperties}>
                {comp.distance_miles > 0 ? `${comp.distance_miles.toFixed(1)} mi` : comp.city}
              </span>
              <span style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 4, color: '#5E636B' }}>
                {comp.distance_miles > 0 ? 'From your home · no photo on file' : 'No photo on file'}
              </span>
            </div>
```

### R17 — /r — comp price

No text on photography: the 70%-black badge over the photo becomes the PDF's solid white price plate, top-left.

**Before**

```tsx
          <div className="absolute top-3 right-3 px-2 py-1 bg-black/70 rounded text-white text-sm font-medium">
```

**After**

```tsx
          <div className="absolute top-2.5 left-2.5 px-2 py-1 bg-white rounded text-sm font-bold" style={{ color: '#14161A' }}>
```

### R18 — /r — comp card

Theme corner on the comp card.

**Before**

```tsx
        className="bg-white rounded-2xl shadow-sm overflow-hidden"
```

**After**

```tsx
        className="bg-white overflow-hidden rounded-[var(--radius)] border border-[#ECECE8]"
```

### R19 — /r — comp $/sqft

The brand colour was used as TEXT on white (l.484). primary is fills only; primary_ink is the text token.

**Before**

```tsx
            <p className="text-center font-semibold" style={{ color: report.branding?.primary_color || '#6366f1' }}>
```

**After**

```tsx
            <p className="text-center font-semibold" style={{ color: 'var(--primary-ink)' }}>
```

### R20 — /r — comp dots

Active dot in the brand fill (l.498), inactive in the PDF axis rule.

**Before**

```tsx
            className={`w-2 h-2 rounded-full transition-colors ${
              i === compIndex ? 'bg-indigo-600' : 'bg-gray-300'
            }`}
```

**After**

```tsx
            className="w-2 h-2 rounded-full transition-colors"
            style={{ background: i === compIndex ? 'var(--primary)' : '#D9DADF' }}
```

### R21 — /r — market $/sqft label

Label follows your data fix: the PDF's median price per square foot. Ship with that change, not before.

**Before**

```tsx
            label="Avg. Price per Sqft"
```

**After**

```tsx
            label="Median price per sq ft"
```

### R22 — /r — market context panel

The indigo-50 panel with violet text (l.536–537) becomes the PDF strip with muted text, and the copy stops asserting "2 miles / 12 months", which the data fix changes to the PDF's window. Print the radius here once it is on the response.

**Before**

```tsx
      <div className="bg-indigo-50 rounded-xl p-4">
        <p className="text-sm text-violet-800">
          Based on {report.comparables.length} comparable sales within 2 miles 
          of your property in the last 12 months.
        </p>
      </div>
```

**After**

```tsx
      <div className="p-4" style={{ background: '#F6F6F3', borderRadius: 'var(--radius)' }}>
        <p className="text-sm m-0" style={{ color: '#5E636B', lineHeight: 1.5 }}>
          Closed sales near your home over the last six months — the same window and radius as your PDF report. A dash means the record is silent, not that the answer is no.
        </p>
      </div>
```

### R23 — /r — agent tab avatar

No violet ring on the photo; the fallback sits on the tint token with the glyph in primary_ink (l.566–570).

**Before**

```tsx
            className="w-24 h-24 rounded-full mx-auto mb-4 object-cover border-4 border-violet-100"
          />
        ) : (
          <div className="w-24 h-24 rounded-full mx-auto mb-4 bg-indigo-100 flex items-center justify-center">
            <User className="w-12 h-12 text-violet-400" />
          </div>
```

**After**

```tsx
            className="w-24 h-24 rounded-full mx-auto mb-4 object-cover"
          />
        ) : (
          <div className="w-24 h-24 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ background: 'var(--tint)', color: 'var(--primary-ink)' }}>
            <User className="w-12 h-12" />
          </div>
```

### R24 — /r — agent card

Theme corner and hairline on the agent card.

**Before**

```tsx
      <div className="bg-white rounded-xl p-6 shadow-sm text-center">
```

**After**

```tsx
      <div className="bg-white p-6 text-center rounded-[var(--radius)] border border-[#ECECE8]">
```

### R25 — /r — call button

Brand fill under on_primary, not white (l.590). FLAG (rule 6 — derived inks). Stripped tel: value.

**Before**

```tsx
            href={`tel:${report.agent.phone}`}
            onClick={() => onContactClick('call')}
            className="flex items-center justify-center gap-3 w-full py-4 text-white rounded-xl font-semibold transition"
            style={{ backgroundColor: report.branding?.primary_color || '#6366f1' }}
```

**After**

```tsx
            href={`tel:${report.agent.phone.replace(/[\s().-]/g, '')}`}
            onClick={() => onContactClick('call')}
            className="flex items-center justify-center gap-3 w-full py-4 font-semibold transition"
            style={{ backgroundColor: 'var(--primary)', color: 'var(--on-primary)', borderRadius: 'var(--radius)' }}
```

### R26 — /r — text button

Border and label in primary_ink — primary is never text on a light surface (l.602). Stripped sms: value.

**Before**

```tsx
            href={`sms:${report.agent.phone}`}
            onClick={() => onContactClick('text')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border-2 rounded-xl font-semibold transition"
            style={{ borderColor: report.branding?.primary_color || '#6366f1', color: report.branding?.primary_color || '#6366f1' }}
```

**After**

```tsx
            href={`sms:${report.agent.phone.replace(/[\s().-]/g, '')}`}
            onClick={() => onContactClick('text')}
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border-2 font-semibold transition"
            style={{ borderColor: 'var(--primary-ink)', color: 'var(--primary-ink)', borderRadius: 'var(--radius)' }}
```

### R27 — /r — email button

Theme corner.

**Before**

```tsx
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition"
```

**After**

```tsx
            className="flex items-center justify-center gap-3 w-full py-4 bg-white border border-gray-300 text-gray-700 rounded-[var(--radius)] font-medium hover:bg-gray-50 transition"
```

### R28 — /r — stat tiles

The indigo glyph goes (l.648); value in the display face, label muted, theme corner and hairline. `icon` stays in the signature so the three call sites are untouched.

**Before**

```tsx
    <div className="bg-white rounded-xl p-3 shadow-sm text-center">
      <div className="text-indigo-600 mb-1 flex justify-center">{icon}</div>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
```

**After**

```tsx
    <div className="bg-white p-3.5 flex flex-col gap-1 rounded-[var(--radius)] border border-[#ECECE8]">
      <p className="m-0" style={{ fontFamily: 'var(--display)', fontWeight: 'var(--display-weight)', fontSize: 24, lineHeight: 1, letterSpacing: 'var(--display-tracking)' } as React.CSSProperties}>{value}</p>
      <p className="m-0" style={{ fontSize: 11.5, color: '#5E636B' }}>{label}</p>
    </div>
```

### R29 — /r — details card

Theme corner and the PDF hairline on the details card, like the other cards (R11, R18, R24).

**Before**

```tsx
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
```

**After**

```tsx
      <div className="bg-white overflow-hidden rounded-[var(--radius)] border border-[#ECECE8]">
```

### R30 — /r — details head

The section head in the PDF label voice (10.5px caps, primary_ink) on the strip, with the hairline.

**Before**

```tsx
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h2 className="font-semibold text-gray-900">Property Details</h2>
        </div>
```

**After**

```tsx
        <div className="px-4 py-3" style={{ background: '#F6F6F3', borderBottom: '1px solid #ECECE8' }}>
          <h2 className="m-0" style={{ fontSize: 10.5, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--primary-ink)', fontWeight: 600 }}>Property details</h2>
        </div>
```
