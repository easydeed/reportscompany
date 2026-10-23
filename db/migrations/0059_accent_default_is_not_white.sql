-- Migration 0059: a new account's accent is not white.
--
-- `accounts.secondary_color` has defaulted to '#ffffff' since 0001, and every
-- reader treats `secondary_color` as the account's ACCENT: the brand resolver,
-- both wizards, the property worker. So every account that never opened the
-- branding page has asked for a white accent on white paper — the white accent
-- on a fresh account's first property report (D-243) and the blank headline
-- number on the Snapshot page (D-256) are this one default.
--
-- Every reader already falls back to a platform colour when the column is
-- empty. The default was what stopped it ever being empty.
--
-- `run_migrations.py` executes each file whole in one transaction; no BEGIN.

-- 1. New accounts: no stored accent, so the platform default applies.
ALTER TABLE accounts ALTER COLUMN secondary_color DROP DEFAULT;

-- 2. Accounts still on BOTH column defaults never chose a colour. Writing
--    NULL there gives them what step 1 gives a new account. An account with
--    a primary colour of its own is left alone even if its accent is white:
--    that row expressed a preference, and this migration does not overrule
--    one. (The branding page's save writes both columns, so "saved without
--    changing anything" lands on the same two defaults and is treated the
--    same — it was not a choice of white either.)
UPDATE accounts
   SET secondary_color = NULL
 WHERE lower(secondary_color) = '#ffffff'
   AND lower(primary_color) = '#03374f';
