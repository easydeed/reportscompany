interface PreviewQuickTakeProps {
  text: string
  accentColor: string
}

export function PreviewQuickTake({ text, accentColor }: PreviewQuickTakeProps) {
  return (
    <div
      className="rounded-md border px-3 py-2.5"
      style={{
        borderColor: `${accentColor}30`,
        backgroundColor: `${accentColor}08`,
      }}
    >
      <div className="mb-1 text-[9px] font-semibold uppercase tracking-wider" style={{ color: accentColor }}>
        Quick Take
      </div>
      <div className="text-[10px] leading-relaxed text-stone-600">{text}</div>
    </div>
  )
}
