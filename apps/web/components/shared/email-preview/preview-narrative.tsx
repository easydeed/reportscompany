interface PreviewNarrativeProps {
  text: string
  primaryColor: string
}

export function PreviewNarrative({ text, primaryColor }: PreviewNarrativeProps) {
  return (
    <div
      className="rounded-md border px-3 py-2.5 text-[11px] leading-relaxed text-stone-600"
      style={{
        borderColor: `${primaryColor}20`,
        backgroundColor: `${primaryColor}06`,
      }}
    >
      <div className="mb-1 flex items-center gap-1.5">
        <div
          className="h-3 w-0.5 rounded-full"
          style={{ backgroundColor: primaryColor }}
        />
        <span className="text-[9px] font-semibold uppercase tracking-wider text-stone-400">
          AI Market Insight
        </span>
      </div>
      {text}
    </div>
  )
}
