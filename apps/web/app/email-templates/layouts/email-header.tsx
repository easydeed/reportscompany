interface EmailHeaderProps {
  reportType: string;
  title: string;
  period?: string;
}

export function EmailHeader({ reportType, title, period = 'Last 30 Days' }: EmailHeaderProps) {
  return (
    <div className="bg-gradient-to-br from-[#1B365D] to-[#B8860B] rounded-t-xl">
      <div className="px-10 py-7 text-center">
        {/* No logo until a caller passes one. A placeholder image with a
            made-up brokerage name would ship the day this layout is used. */}

        {/* Report Type Badge */}
        <span className="inline-block bg-white/20 text-white text-[11px] font-semibold uppercase tracking-wider px-4 py-1.5 rounded-full mb-3">
          {reportType}
        </span>

        {/* Title */}
        <h1 className="text-white text-[26px] font-light tracking-tight leading-tight mb-2">
          {title}
        </h1>

        {/* Period */}
        <p className="text-white/90 text-sm">
          {period} &bull; Live MLS Data
        </p>
      </div>

      {/* Accent Strip */}
      <div className="h-1 bg-gradient-to-r from-[#1B365D] to-[#B8860B]" />
    </div>
  );
}
