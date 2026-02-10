# PDFShift Integration

## Overview

PDFShift provides cloud-based HTML-to-PDF rendering for production report generation.

## Service Details

- **Used by:** Worker service (`pdf_engine.py`) in production environment
- **API endpoint:** `POST https://api.pdfshift.io/v3/convert/pdf`
- **Auth method:** API Key

## Configuration

- **Margins:** Zero margins (CSS handles all layout and spacing)
- **Network:** `wait_for_network` enabled to ensure all resources load
- **Images:** `lazy_load_images` enabled for complete image rendering
- **Timeout:** 100 seconds

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PDFSHIFT_API_KEY` | PDFShift API key |

## Key Behaviors

- PDFShift is the production PDF renderer; Playwright is used in development
- HTML content is sent to PDFShift with zero margins (page layout is fully controlled by CSS)
- The `wait_for_network` option ensures all external resources (fonts, images, stylesheets) are loaded before rendering
- `lazy_load_images` ensures images that use lazy loading are fully rendered
- 100-second timeout accommodates complex reports with many images
- On failure, the worker retries with an extended timeout before marking the report as failed
