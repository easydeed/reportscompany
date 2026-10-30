-- Migration 0062: email_log.status says what it holds (D-083).
--
-- 0027's COMMENT lists four values (sent, suppressed, failed, unknown). Since
-- then the code has written four more, and three of them are NOT deliveries,
-- which is the one distinction anyone reading the comment needs. The admin
-- counters (`routes/admin.py`) count only sent/sending/failed for that reason.
--
-- Values, and their writers:
--   sending               attempt recorded before the provider call (worker tasks.py, D-065)
--   sent                  the provider accepted it
--   failed                the provider refused it, or the send raised
--   suppressed            not sent on purpose: the provider suppressed it, the
--                         worker had no email key, or the report matched no
--                         listings (D-110)
--   duplicate_suppressed  a redelivered run refused because it was already delivered (#61)
--   blocked_unverified    refused because the account's email is unverified (D-019)
--   queued                the company test email, before its send (routes/company.py)
--   unknown               historical rows only; nothing writes it now
--
-- A COMMENT only: no data or constraint changes, and nothing reads it at runtime.
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

COMMENT ON COLUMN email_log.status IS
  'Delivery status. Deliveries: sending (attempt recorded before the provider call), sent, failed. '
  'Not deliveries: suppressed (provider-suppressed, no email key, or a report that matched nothing), '
  'duplicate_suppressed (a redelivery refused), blocked_unverified (unverified account email), '
  'queued (company test email before its send). unknown: historical rows only.';
