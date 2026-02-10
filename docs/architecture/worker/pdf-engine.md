# PDF Engine

> `apps/worker/src/worker/pdf_engine.py` (286 lines)
> Dual-backend PDF rendering: Playwright (local) + PDFShift (production)

## Architecture

The PDF engine abstracts PDF rendering behind a simple interface. The `PDF_ENGINE` environment variable controls which backend is used.

### Backend: Playwright (Local Development)

- Launches headless Chromium
- Navigates to `/print/{run_id}` on the frontend
- Waits for `networkidle` state
- Renders Letter-size PDF (8.5" x 11") with 0.5" margins
- Fast, free, but requires browser binary

### Backend: PDFShift (Production)

- Cloud API: `POST https://api.pdfshift.io/v3/convert/pdf`
- Zero margins (CSS `@page { margin: 0 }` handles layout)
- Image loading: 5-8 second delay + `wait_for_network: true` + `lazy_load_images: true`
- 100 second timeout
- Removes blank trailing pages
- Returns raw PDF bytes

## API

```python
render_pdf(run_id, account_id, html_content=None, print_base=None) -> Tuple[str, str]
```

- `run_id` -- Report ID for constructing print page URL
- `account_id` -- For logging/tracking
- `html_content` -- Optional raw HTML (skips print page)
- `print_base` -- Override frontend URL (default: PRINT_BASE env var)

Returns a tuple of `(pdf_path, print_url)` -- the local path to the generated PDF and the source URL that was rendered.

## Print Pipeline

```
Frontend: /print/[runId]       -- Server-rendered HTML page
  -> Worker: pdf_engine.py     -- Captures HTML, converts to PDF
    -> Playwright or PDFShift  -- Headless browser or cloud API
      -> R2 upload             -- Stores PDF, returns presigned URL
```

## PDFShift Configuration Details

The PDFShift payload includes several critical options:

| Option | Value | Purpose |
|--------|-------|---------|
| `sandbox` | `false` | Use production rendering |
| `use_print` | `true` | Apply `@media print` stylesheets |
| `format` | `Letter` | US Letter (8.5" x 11") |
| `margin` | All `"0"` | Zero margins -- CSS `@page { margin: 0 }` handles layout |
| `remove_blank` | `true` | Strip blank trailing pages |
| `delay` | 5000-8000ms | Wait for images to load before capture |
| `wait_for_network` | `true` | Wait for network to go idle (no requests for 500ms) |
| `lazy_load_images` | `true` | Scroll to trigger lazy-loaded images |
| `timeout` | 100s | Maximum conversion time |

Authentication uses `X-API-Key` header (not Basic Auth). The `X-Processor-Version: 142` header enables the newer conversion engine with better CSS3 support.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PDF_ENGINE` | `playwright` or `pdfshift` | `playwright` |
| `PDFSHIFT_API_KEY` | PDFShift API key | None |
| `PDFSHIFT_API_URL` | PDFShift endpoint | `https://api.pdfshift.io/v3/convert/pdf` |
| `PRINT_BASE` | Frontend URL for print pages | `http://localhost:3000` |
| `PDF_DIR` | Temp directory for PDFs | `/tmp/mr_reports` |
