interface PdfPageIndicatorProps {
  page?: number
  totalPages: number
}

// Subtle "Page 1 of N" footer text. PDFs rendered by the worker have their own
// page numbering — this is purely a hint that the preview only shows page 1.
export function PdfPageIndicator({ page = 1, totalPages }: PdfPageIndicatorProps) {
  return (
    <div className="px-4 pb-1.5 text-right text-[7px] uppercase tracking-wider text-stone-400">
      Page {page} of {totalPages}
    </div>
  )
}
