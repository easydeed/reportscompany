interface PreviewHeroStatProps {
  label: string
  value: string
  sub?: string
  primaryColor: string
}

export function PreviewHeroStat({ label, value, sub, primaryColor }: PreviewHeroStatProps) {
  return (
    <div className="text-center py-2">
      <div className="text-[9px] font-semibold uppercase tracking-wider text-stone-400">
        {label}
      </div>
      <div
        className="text-[28px] font-bold leading-none mt-0.5"
        style={{ color: primaryColor, fontFamily: "Georgia, 'Times New Roman', serif" }}
      >
        {value}
      </div>
      {sub && (
        <div className="mt-0.5 text-[10px] text-stone-500">{sub}</div>
      )}
    </div>
  )
}
