interface PdfAgentFooterProps {
  agentName: string
  agentTitle: string | null
  agentPhone: string | null
  agentEmail: string
  agentPhotoUrl: string | null
  primaryColor: string
  accentColor: string
}

// Bottom band of the printed page. Mirrors the agent-card section used on the
// last page of every market report PDF.
export function PdfAgentFooter({
  agentName,
  agentTitle,
  agentPhone,
  agentEmail,
  agentPhotoUrl,
  primaryColor,
  accentColor,
}: PdfAgentFooterProps) {
  return (
    <div
      className="flex items-center gap-2.5 border-t-2 px-4 py-2.5"
      style={{ borderColor: primaryColor }}
    >
      <div
        className="flex h-9 w-9 flex-shrink-0 items-center justify-center overflow-hidden rounded-full bg-stone-100"
        style={{ border: `1.5px solid ${accentColor}55` }}
      >
        {agentPhotoUrl ? (
          <img src={agentPhotoUrl} alt={agentName} className="h-full w-full object-cover" />
        ) : (
          <span className="text-[10px] font-semibold text-stone-400">
            {agentName?.charAt(0) || "?"}
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[10px] font-bold text-stone-900 leading-tight">
          {agentName}
        </div>
        {agentTitle && (
          <div className="text-[7px] text-stone-500">{agentTitle}</div>
        )}
      </div>
      <div className="flex flex-col items-end text-[7.5px] text-stone-600">
        {agentPhone && <span>{agentPhone}</span>}
        {agentEmail && <span>{agentEmail}</span>}
      </div>
    </div>
  )
}
