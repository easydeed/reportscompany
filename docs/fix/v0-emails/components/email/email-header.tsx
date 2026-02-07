export function EmailHeader() {
  return (
    <>
      <div
        className="rounded-t-lg px-8 py-10 text-center"
        style={{
          background: "linear-gradient(135deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      >
        <div className="mb-4 inline-block rounded-full border border-white/20 bg-white/10 px-4 py-1.5">
          <span className="text-xs font-medium uppercase tracking-widest text-white/90">
            Acme Realty
          </span>
        </div>
        <h1 className="text-balance font-serif text-3xl font-bold tracking-tight text-white">
          Market Snapshot &ndash; Los Angeles
        </h1>
        <p className="mt-3 text-sm text-white/80">
          Period: Last 30 Days &bull; Source: Live MLS Data
        </p>
      </div>
      {/* Accent Transition Strip */}
      <div
        className="h-1"
        style={{
          background: "linear-gradient(90deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      />
    </>
  );
}

export function GalleryHeader() {
  return (
    <>
      <div
        className="rounded-t-lg px-8 py-10 text-center"
        style={{
          background: "linear-gradient(135deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      >
        <div className="mb-4 inline-block rounded-full border border-white/20 bg-white/10 px-4 py-1.5">
          <span className="text-xs font-medium uppercase tracking-widest text-white/90">
            Acme Realty
          </span>
        </div>
        <h1 className="text-balance font-serif text-3xl font-bold tracking-tight text-white">
          New Listings &ndash; Los Angeles
        </h1>
        <p className="mt-3 text-sm text-white/80">
          Period: Last 30 Days &bull; Source: Live MLS Data
        </p>
      </div>
      <div
        className="h-1"
        style={{
          background: "linear-gradient(90deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      />
    </>
  );
}

export function TableHeader() {
  return (
    <>
      <div
        className="rounded-t-lg px-8 py-10 text-center"
        style={{
          background: "linear-gradient(135deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      >
        <div className="mb-4 inline-block rounded-full border border-white/20 bg-white/10 px-4 py-1.5">
          <span className="text-xs font-medium uppercase tracking-widest text-white/90">
            Acme Realty
          </span>
        </div>
        <h1 className="text-balance font-serif text-3xl font-bold tracking-tight text-white">
          Recent Sales &ndash; Los Angeles
        </h1>
        <p className="mt-3 text-sm text-white/80">
          Period: Last 30 Days &bull; Source: Live MLS Data
        </p>
      </div>
      <div
        className="h-1"
        style={{
          background: "linear-gradient(90deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      />
    </>
  );
}

export function AnalyticsHeader() {
  return (
    <>
      <div
        className="rounded-t-lg px-8 py-10 text-center"
        style={{
          background: "linear-gradient(135deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      >
        <div className="mb-4 inline-block rounded-full border border-white/20 bg-white/10 px-4 py-1.5">
          <span className="text-xs font-medium uppercase tracking-widest text-white/90">
            Acme Realty
          </span>
        </div>
        <h1 className="text-balance font-serif text-3xl font-bold tracking-tight text-white">
          Market Analytics &ndash; Los Angeles
        </h1>
        <p className="mt-3 text-sm text-white/80">
          12-Month Trends &bull; Source: Live MLS Data
        </p>
      </div>
      <div
        className="h-1"
        style={{
          background: "linear-gradient(90deg, #1e3a5f 0%, #b8860b 100%)",
        }}
      />
    </>
  );
}
