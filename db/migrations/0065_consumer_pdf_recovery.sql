-- Migration 0065: a delivered report's missing PDF can be generated, once (LR-022, D-380).
--
-- A consumer report whose PDF render failed during delivery was delivered with
-- no PDF, and the download button polled forever. These record the PDF's own
-- small state machine, separate from the delivery's (LR-020):
--   pdf_status      NULL (none yet) | queued | generating | ready | failed
--   pdf_claimed_at  when the current queue/generation claim was taken; a claim
--                   older than the window is stale and may be taken again
--   pdf_claim_id    the claim, so only its owner can finish or fail it; also
--                   names the new generation-keyed object
--   pdf_error       why the last generation failed (no contact details)
--   pdf_object_key  the stored object; the API re-signs a fresh link from it on
--                   each download (Jerry, 2026-11-11), because a stored
--                   presigned URL stops working after 7 days
--
-- Additive and nullable, no defaults, no backfill. A missing PDF is rendered
-- into a NEW object and never replaces one (Jerry, 2026-11-11).
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

SET LOCAL lock_timeout = '5s';

ALTER TABLE consumer_reports
  ADD COLUMN IF NOT EXISTS pdf_status      TEXT,
  ADD COLUMN IF NOT EXISTS pdf_claimed_at  TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS pdf_claim_id    UUID,
  ADD COLUMN IF NOT EXISTS pdf_error       TEXT,
  ADD COLUMN IF NOT EXISTS pdf_object_key  TEXT;

COMMENT ON COLUMN consumer_reports.pdf_status IS
  'The PDF: NULL (none yet), queued, generating, ready, failed (LR-022). Separate from the delivery status.';
COMMENT ON COLUMN consumer_reports.pdf_claimed_at IS
  'When the current PDF queue/generation claim was taken; older than the window is stale.';
COMMENT ON COLUMN consumer_reports.pdf_claim_id IS
  'The current PDF generation claim; names its generation-keyed object.';
COMMENT ON COLUMN consumer_reports.pdf_error IS
  'Why the last PDF generation failed. No contact details.';
COMMENT ON COLUMN consumer_reports.pdf_object_key IS
  'The stored PDF object. Downloads get a freshly signed link from it (stored presigned URLs expire after 7 days).';
