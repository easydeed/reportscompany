-- =============================================
-- Migration 0045: Allow NULL consumer_phone
-- =============================================
-- When delivery_method is 'email', consumer_phone may be NULL.
-- The NOT NULL constraint was left from the original SMS-only design.

ALTER TABLE consumer_reports ALTER COLUMN consumer_phone DROP NOT NULL;
