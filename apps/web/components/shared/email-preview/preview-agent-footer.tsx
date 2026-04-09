interface PreviewAgentFooterProps {
  agentName: string
  agentTitle?: string | null
  agentPhone?: string | null
  agentEmail?: string | null
  agentPhotoUrl?: string | null
  agentLogoUrl?: string | null
  primaryColor: string
  accentColor?: string
}

export function PreviewAgentFooter({
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  agentLogoUrl,
  primaryColor,
  accentColor,
}: PreviewAgentFooterProps) {
  const accent = accentColor || primaryColor

  return (
    <div className="flex items-center gap-3 border-t border-stone-200 pt-3">
      <div
        className="flex h-14 w-14 flex-shrink-0 items-center justify-center overflow-hidden rounded-full bg-stone-100"
        style={{ border: `2px solid ${accent}40` }}
      >
        {agentPhotoUrl ? (
          <img
            src={agentPhotoUrl}
            alt={agentName}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="text-lg font-semibold text-stone-400">
            {agentName?.charAt(0) || "?"}
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div
          className="text-[16px] font-bold text-stone-900"
          style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
        >
          {agentName}
        </div>
        {agentTitle && (
          <div className="text-[9px] text-stone-500">{agentTitle}</div>
        )}
        {(agentPhone || agentEmail) && (
          <div className="mt-1 flex flex-wrap gap-1">
            {agentPhone && (
              <span
                className="inline-block rounded-full px-2 py-0.5 text-[8px] font-medium"
                style={{ color: accent, border: `1px solid ${accent}40` }}
              >
                {agentPhone}
              </span>
            )}
            {agentEmail && (
              <span
                className="inline-block rounded-full px-2 py-0.5 text-[8px] font-medium"
                style={{ color: accent, border: `1px solid ${accent}40` }}
              >
                {agentEmail}
              </span>
            )}
          </div>
        )}
      </div>
      {agentLogoUrl && (
        <img
          src={agentLogoUrl}
          alt="Company"
          className="h-auto max-w-[80px] flex-shrink-0 object-contain opacity-70"
          style={{ maxHeight: 28 }}
        />
      )}
    </div>
  )
}
