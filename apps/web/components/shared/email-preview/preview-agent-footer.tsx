interface PreviewAgentFooterProps {
  agentName: string
  agentTitle?: string | null
  agentPhone?: string | null
  agentEmail?: string | null
  agentPhotoUrl?: string | null
  primaryColor: string
}

export function PreviewAgentFooter({
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  primaryColor,
}: PreviewAgentFooterProps) {
  const contactParts = [agentPhone, agentEmail].filter(Boolean)

  return (
    <div className="flex items-center gap-2.5 border-t border-stone-200 pt-3">
      <div
        className="flex h-10 w-10 flex-shrink-0 items-center justify-center overflow-hidden rounded-full bg-stone-100"
        style={{ border: `2px solid ${primaryColor}` }}
      >
        {agentPhotoUrl ? (
          <img
            src={agentPhotoUrl}
            alt={agentName}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="text-sm font-semibold text-stone-400">
            {agentName?.charAt(0) || "?"}
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-semibold text-stone-900">{agentName}</div>
        {agentTitle && (
          <div className="text-[9px] text-stone-500">{agentTitle}</div>
        )}
        {contactParts.length > 0 && (
          <div className="text-[9px]" style={{ color: primaryColor }}>
            {contactParts.join(" \u2022 ")}
          </div>
        )}
      </div>
    </div>
  )
}
