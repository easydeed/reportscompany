# Edits — the digital report, round 2 (/p/[code] and /r/[id])

Cut against `easydeed/reportscompany` **main** as read 2026-11-05T17:18Z (tree `15b80ddd9d46`). `401f5ba6...main` touches none of the three live files (checked by compare), so these anchors hold for `401f5ba6` and every commit after it as of this reading. Three live files, 21 anchored touches making 7 edits (F7, R9, R22, B1, B2, B3 — R21 dropped, see README). Apply with `apply_touches.py` (`--check` first); it refuses if any anchor moved. `touches.json` is the source of this document.

Fixed-rule flags are **FLAG (rule 6)** in the *why*. The one data dependency (rule 5 — yours) is the 410 body carrying `theme` and `theme_tokens`; B3b reads them with a null fallback so it builds before that lands.

| edit | touches | file(s) |
|---|---|---|
| F7 — consent | F7a–F7e | lead-capture-form.tsx, page.tsx |
| R9 — range panel | R9 | MobileReportViewer.tsx |
| R22 — market context | R22 | MobileReportViewer.tsx |
| B1 — four tabs | B1a–B1f | MobileReportViewer.tsx |
| B2 — phone agent line | B2 | page.tsx |
| B3 — status page | B3a–B3g | page.tsx |


## `apps/web/app/p/[code]/page.tsx`

### F7d — /p — form mount

Part of F7: `/p` stops passing `accentColor` to the form.

**Before**

```tsx
                agentName={data.agent_name}
                accentColor={accentColor}
              />
```

**After**

```tsx
                agentName={data.agent_name}
              />
```

### F7e — /p — page setup

Part of F7: the `const accentColor` line (`data.accent_color || "#2563eb"`) was the last raw colour read on /p. Removed; nothing reads it after F7d. The `accent_color` field stays on the response type — it describes the API, not the page.

**Before**

```tsx
  const accentColor = data.accent_color || "#2563eb";

```

**After**

```tsx

```

### B2 — /p — phone agent line

B2: on a phone, one line above the form says whom the visitor is writing to — the footer’s own pattern (name in ink, ` · company` when present, phone as tap-to-call in `primary_ink`), under a hairline. `md:hidden`, so from `md` up the agent panel is first as today. Renders only when `agent_name` is set; no placeholder. The full agent panel and the `order-*` classes are untouched.

**Before**

```tsx
            {/* Lead form — first on a phone */}
            <div className="order-1 md:order-2 p-5 md:p-10 bg-white">
              <span className="block mb-2" style={{ fontSize: 10.5, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--primary-ink)", fontWeight: 600 }}>
```

**After**

```tsx
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
```

### B3a — /p — fetch result type

B3: the inactive, expired and locked results can carry `theme` and `theme_tokens`, optional. Not-found and error carry nothing — no account to theme from.

**Before**

```tsx
type FetchResult = 
  | { status: "success"; data: PropertyReportData }
  | { status: "not_found" }
  | { status: "inactive"; message: string }
  | { status: "expired"; message: string }
  | { status: "requires_code" }
  | { status: "error"; message: string };
```

**After**

```tsx
type FetchResult = 
  | { status: "success"; data: PropertyReportData }
  | { status: "not_found" }
  | { status: "inactive"; message: string; theme?: number | null; theme_tokens?: ThemeTokens | null }
  | { status: "expired"; message: string; theme?: number | null; theme_tokens?: ThemeTokens | null }
  | { status: "requires_code"; theme?: number | null; theme_tokens?: ThemeTokens | null }
  | { status: "error"; message: string };
```

### B3b — /p — 410 branch

B3: expired and inactive read `theme` and `theme_tokens` from the 410 body you are adding (rule 5, yours). Absent fields read as null and the page falls back to NEUTRAL_TOKENS, so this builds and renders before the API change lands. Message handling unchanged.

**Before**

```tsx
      const message = data.detail || "This page is no longer available";
      if (message.includes("expired")) {
        return { status: "expired", message };
      }
      return { status: "inactive", message };
```

**After**

```tsx
      const message = data.detail || "This page is no longer available";
      const theme = data.theme ?? null;
      const theme_tokens = data.theme_tokens ?? null;
      if (message.includes("expired")) {
        return { status: "expired", message, theme, theme_tokens };
      }
      return { status: "inactive", message, theme, theme_tokens };
```

### B3c — /p — locked branch

B3: locked already receives the full response; pass its `theme` and `theme_tokens` through.

**Before**

```tsx
    if (data.requires_access_code) {
      return { status: "requires_code" };
    }
```

**After**

```tsx
    if (data.requires_access_code) {
      return { status: "requires_code", theme: data.theme ?? null, theme_tokens: data.theme_tokens ?? null };
    }
```

### B3d — /p — StatusPage

B3: the status page wears the theme. Faces from `THEME_FACES` via `themeName(theme)`, colours from tokens (`NEUTRAL_TOKENS` and the default faces when none — not-found, error, or before the 410 body carries them). PDF strip page, white sheet with the theme corner and hairline, an 8px brand bar across the top (a surface with no text on it), icon in `primary_ink`, title in the display face, message muted, the PDF foot. No Tailwind hue class remains (amber/slate/red/blue icons gone). Each case’s text is unchanged. FLAG (rule 6 — brand colour as a surface; no text sits on it).

**Before**

```tsx
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
```

**After**

```tsx
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
```

### B3e — /p — inactive mount

B3: the inactive case passes its theme and tokens through. Text unchanged.

**Before**

```tsx
        icon="inactive"
        title="Page Not Available"
        message={result.message}
      />
```

**After**

```tsx
        icon="inactive"
        title="Page Not Available"
        message={result.message}
        theme={result.theme}
        tokens={result.theme_tokens}
      />
```

### B3f — /p — expired mount

B3: the expired case passes its theme and tokens through. Text unchanged.

**Before**

```tsx
        icon="expired"
        title="Page Expired"
        message={result.message}
      />
```

**After**

```tsx
        icon="expired"
        title="Page Expired"
        message={result.message}
        theme={result.theme}
        tokens={result.theme_tokens}
      />
```

### B3g — /p — locked mount

B3: the locked case passes the theme and tokens it already receives. Text unchanged. The error mount is left as is — it has no account, so it renders on NEUTRAL_TOKENS by default.

**Before**

```tsx
        icon="locked"
        title="Access Code Required"
        message="This property page is protected. Please enter the access code to continue."
      />
```

**After**

```tsx
        icon="locked"
        title="Access Code Required"
        message="This property page is protected. Please enter the access code to continue."
        theme={result.theme}
        tokens={result.theme_tokens}
      />
```

## `apps/web/app/p/[code]/lead-capture-form.tsx`

### F7a — /p — consent checkbox + label

Re-cut of F7 against #265. The box keeps `required` (yours, live). Added: 20px hit area, border-slate-400 so the box reads on white, `accent-color` from the theme (`var(--primary)`, a token — the last raw colour read on /p goes in F7b–F7e). The label still prints `P_CONSENT_COPY` as its only child, exactly; the asterisk is a sibling span outside the label (aria-hidden) so the label text equals `leads.consent_text` byte for byte. No wording touched.

**Before**

```tsx
          required
          className="mt-1 w-4 h-4 rounded border-slate-300"
          style={{ accentColor }}
          disabled={status === "submitting"}
        />
        <label 
          htmlFor="consent_given" 
          className="text-sm text-slate-600"
        >
          {P_CONSENT_COPY}
        </label>
```

**After**

```tsx
          required
          className="mt-0.5 w-5 h-5 rounded border-slate-400"
          style={{ accentColor: "var(--primary)" }}
          disabled={status === "submitting"}
        />
        <span className="text-[13px] leading-normal" style={{ color: "#2A2D33" }}>
          <label htmlFor="consent_given">{P_CONSENT_COPY}</label>
          <span aria-hidden="true" style={{ color: "var(--primary-ink)" }}> *</span>
        </span>
```

### F7b — /p — form props type

Part of F7: the checkbox no longer reads `accentColor`, so the prop goes end to end. The field leaves the props type.

**Before**

```tsx
  agentName: string | null;
  accentColor: string;
}
```

**After**

```tsx
  agentName: string | null;
}
```

### F7c — /p — form destructure

Part of F7: the destructure drops `accentColor`.

**Before**

```tsx
  shortCode, 
  agentName, 
  accentColor 
}: LeadCaptureFormProps) {
```

**After**

```tsx
  shortCode, 
  agentName
}: LeadCaptureFormProps) {
```

## `apps/web/components/mobile-report/MobileReportViewer.tsx`

### R9 — /r — range panel (Overview hero)

Re-cut of R9 against #265. The last direct brand read in the file — `linear-gradient(primary_color → accent_color)` under `text-violet-200` — becomes the PDF range panel (`.rangepanel`, report.jinja2 l.370–377) on the fixed dark neutral: label in `primary_on_dark`, the range in the display face at 34px/0.95, method line and basis in the PDF’s 80% white at 13/12px. Content is exactly the four strings and the no-range line already on the card: `RANGE_HEADING`, low – high, `comps_range.method`, `rangeBasis(comps_range)`, `NO_RANGE`. No midpoint, no "most likely", no figure that isn’t a comp. FLAG (rule 6 — estimate panel; text on gradients removed; derived inks).

**Before**

```tsx
      {/* Hero Card */}
      <div className="rounded-2xl p-6 text-white" style={{ background: `linear-gradient(135deg, ${report.branding?.primary_color || '#6366f1'} 0%, ${report.branding?.accent_color || '#8b5cf6'} 100%)` }}>
        <p className="text-violet-200 text-sm mb-1">{RANGE_HEADING}</p>
        {report.comps_range ? (
          <>
            <p className="text-3xl font-bold mb-2">
              {formatPrice(report.comps_range.low)} – {formatPrice(report.comps_range.high)}
            </p>
            <p className="text-violet-200 text-sm">{report.comps_range.method}</p>
            <p className="mt-4 text-violet-200 text-xs">{rangeBasis(report.comps_range)}</p>
          </>
        ) : (
          <p className="text-base">{NO_RANGE}</p>
        )}
      </div>
```

**After**

```tsx
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
```

### R22 — /r — market context panel

Re-cut of R22 against #265. `bg-indigo-50` / `text-violet-800` becomes the PDF strip (`#F6F6F3`, `.notonrecord` l.339) with muted text (`#5E636B`), plus the hairline so the strip reads on the strip-coloured page. `{compsSentence(stats)}` stays as the content, untouched. After R9 and R22 the file names no Tailwind indigo or violet class.

**Before**

```tsx
      <div className="bg-indigo-50 rounded-xl p-4">
        <p className="text-sm text-violet-800">
          {compsSentence(stats)}
        </p>
      </div>
```

**After**

```tsx
      <div className="p-4" style={{ background: '#F6F6F3', border: '1px solid #ECECE8', borderRadius: 'var(--radius)' }}>
        <p className="text-sm m-0" style={{ color: '#5E636B', lineHeight: 1.5 }}>
          {compsSentence(stats)}
        </p>
      </div>
```

### B1a — /r — tab id type

B1: four tabs. `details` leaves the `TabId` union.

**Before**

```tsx
type TabId = 'overview' | 'details' | 'comps' | 'market' | 'agent';
```

**After**

```tsx
type TabId = 'overview' | 'comps' | 'market' | 'agent';
```

### B1b — /r — tabs array

B1: the Details entry leaves the tab bar. Order stays Overview · Comps · Market · Agent.

**Before**

```tsx
  { id: 'details', label: 'Details', icon: Building2 },

```

**After**

```tsx

```

### B1c — /r — icon import

B1: `Building2` had one use, the Details tab. Dropped from the import so lint stays clean.

**Before**

```tsx
  Home, Building2, TrendingUp, BarChart3, User,
```

**After**

```tsx
  Home, TrendingUp, BarChart3, User,
```

### B1d — /r — tab switch

B1: the `details` branch leaves the `activeTab` switch.

**Before**

```tsx
            {activeTab === 'details' && (
              <DetailsTab report={report} />
            )}

```

**After**

```tsx

```

### B1e — /r — DetailsTab component

B1: the component goes. Every field it showed is on Overview exactly once after B1f: address/city/state/ZIP (address card), beds/baths/sqft (the three tiles), lot size and year built (B1f).

**Before**

```tsx
function DetailsTab({ report }: { report: ReportData }) {
  const details = [
    { label: 'Address', value: report.property.address },
    { label: 'City', value: report.property.city },
    { label: 'State', value: report.property.state },
    { label: 'ZIP', value: report.property.zip },
    { label: 'Bedrooms', value: report.property.bedrooms || '—' },
    { label: 'Bathrooms', value: report.property.bathrooms || '—' },
    { label: 'Square Feet', value: report.property.sqft?.toLocaleString() || '—' },
    { label: 'Lot Size', value: report.property.lot_size ? `${report.property.lot_size.toLocaleString()} sqft` : '—' },
    { label: 'Year Built', value: report.property.year_built || '—' },
  ];

  return (
    <div className="p-4">
      <div className="bg-white overflow-hidden rounded-[var(--radius)] border border-[#ECECE8]">
        <div className="px-4 py-3" style={{ background: '#F6F6F3', borderBottom: '1px solid #ECECE8' }}>
          <h2 className="m-0" style={{ fontSize: 10.5, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--primary-ink)', fontWeight: 600 }}>Property details</h2>
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



```

**After**

```tsx

```

### B1f — /r — Overview address card

B1: lot size and year built, the two Details facts Overview lacked, join the address card as a two-up facts row under a hairline — display-face value, muted label, same voice as the three tiles. Same fields and formatting DetailsTab used (`lot_size.toLocaleString()` + " sqft"; `year_built`); missing prints `—`, never 0 (fixed rule). Fields already on the response; no data change.

**Before**

```tsx
      {/* Address Card */}
      <div className="bg-white p-4 rounded-[var(--radius)] border border-[#ECECE8]">
        <div className="flex items-start gap-3">
          <div>
            <p className="font-semibold text-gray-900">{report.property.address}</p>
            <p className="text-gray-600">
              {report.property.city}, {report.property.state} {report.property.zip}
            </p>
          </div>
        </div>
      </div>
```

**After**

```tsx
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
```
