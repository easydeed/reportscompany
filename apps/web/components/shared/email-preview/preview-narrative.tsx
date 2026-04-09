interface PreviewNarrativeProps {
  text: string
  primaryColor: string
  accentColor?: string
}

export function PreviewNarrative({ text, accentColor, primaryColor }: PreviewNarrativeProps) {
  const color = accentColor || primaryColor

  return (
    <div
      className="rounded-md border px-3 py-2.5 text-[11px] leading-relaxed text-stone-600"
      style={{
        borderColor: `${color}40`,
        backgroundColor: `${color}06`,
      }}
    >
      <div className="mb-1 flex items-center gap-1.5">
        <div
          className="h-3 w-0.5 rounded-full"
          style={{ backgroundColor: color }}
        />
        <span className="text-[9px] font-semibold uppercase tracking-wider" style={{ color }}>
          Market Insight
        </span>
      </div>
      {text}
    </div>
  )
}
