interface PreviewGalleryCountProps {
  count: number
  label: string
  accentColor: string
}

export function PreviewGalleryCount({ count, label, accentColor }: PreviewGalleryCountProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-1">
      <div
        className="flex h-7 w-7 items-center justify-center rounded-full text-[11px] font-bold text-white"
        style={{ backgroundColor: accentColor }}
      >
        {count}
      </div>
      <span className="text-[11px] font-medium text-stone-600">{label}</span>
    </div>
  )
}
