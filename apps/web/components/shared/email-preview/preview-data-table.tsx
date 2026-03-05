import type { SampleTableRow } from "./sample-data"

interface PreviewDataTableProps {
  rows: SampleTableRow[]
  primaryColor: string
}

export function PreviewDataTable({ rows, primaryColor }: PreviewDataTableProps) {
  if (rows.length === 0) return null

  return (
    <div className="overflow-hidden rounded-md border border-stone-200">
      <div
        className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-2 px-2.5 py-1.5 text-[8px] font-semibold uppercase tracking-wider text-white"
        style={{ backgroundColor: primaryColor }}
      >
        <div>Address</div>
        <div className="text-center">Bd</div>
        <div className="text-center">Ba</div>
        <div className="text-right">Price</div>
        <div className="text-right">DOM</div>
      </div>
      {rows.map((row, i) => (
        <div
          key={i}
          className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-2 border-t border-stone-100 px-2.5 py-1.5 text-[9px]"
        >
          <div className="truncate font-medium text-stone-700">{row.address}</div>
          <div className="text-center text-stone-500 w-5">{row.beds}</div>
          <div className="text-center text-stone-500 w-5">{row.baths}</div>
          <div className="text-right font-semibold text-stone-800 w-12">{row.price}</div>
          <div className="text-right text-stone-400 w-6">{row.dom}</div>
        </div>
      ))}
    </div>
  )
}
