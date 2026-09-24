-- Migration 0057: clear the "view in browser" links that point at the wrong report.
--
-- D-101. `report_generations.html_url` holds `{PRINT_BASE}/print/{id}` for every
-- market report ever generated. The worker wrote it there because `render_pdf`
-- returned that URL unconditionally — including when it had just rendered the
-- PDF from an `html_content` string, in which case the URL produced none of it.
--
-- The app surfaces the column as a "view in browser" link in three places
-- (components/report-builder/index.tsx:213, app/app/reports/[id]/page.tsx:292,
-- app/app/reports/page.tsx:107). That route does not render the report that was
-- generated. It renders the LEGACY build — apps/web/app/print/[runId]/page.tsx
-- and the seven apps/web/templates/trendy-*.html files — which paginates at a
-- fixed 15 rows a page against the PDF's 13-then-25, carries no themed header,
-- no Outfit, and no AI narrative. A customer clicking it sees a visibly
-- different document from the one attached to their email.
--
-- The code fix stops new rows being written that way. It is forward-only: every
-- row already in the table keeps its link, and the app keeps showing it. This
-- migration is the other half.
--
-- WHY NULL AND NOT A REPAIR. There is no correct value to write. The document
-- the customer was sent is the PDF, and `pdf_url` already points at it; nothing
-- serves the rendered HTML of a market report at a URL. NULL is what the column
-- means when no browser-viewable rendering exists, all three call sites guard on
-- truthiness, and the link simply stops appearing. Restoring the feature means
-- serving the real HTML, which is a separate piece of work.
--
-- WHY THIS LOSES NOTHING. The value is `{PRINT_BASE}/print/{id}` — derivable
-- from the row's own id and an environment variable. Nothing is destroyed that
-- cannot be reconstructed, and what is reconstructed is the wrong document.
--
-- SCOPE. Only rows whose html_url is that print path. A row holding anything
-- else was written by some other route and is not this defect's to clear.

UPDATE report_generations
   SET html_url = NULL
 WHERE html_url IS NOT NULL
   AND html_url LIKE '%/print/%';

-- Verify: expect 0 rows.
SELECT count(*) AS remaining_print_links
  FROM report_generations
 WHERE html_url LIKE '%/print/%';
