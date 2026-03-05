interface PreviewCtaProps {
  primaryColor: string
}

export function PreviewCta({ primaryColor }: PreviewCtaProps) {
  return (
    <div
      className="rounded-md px-4 py-3 text-center"
      style={{ backgroundColor: `${primaryColor}08` }}
    >
      <div
        className="inline-block rounded-md px-5 py-2 text-[11px] font-semibold text-white"
        style={{ backgroundColor: primaryColor }}
      >
        View Full Report &rarr;
      </div>
    </div>
  )
}
