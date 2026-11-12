-- 0067 — LR-025 (D-383): the Home Value Page's stored description stops
-- promising a home's worth.
--
-- 0039 gave users.landing_page_subheadline the DEFAULT 'Find out what your
-- home is worth in today''s market.' Adding a column with a default fills it
-- into every existing row, so that sentence became the stored description of
-- nearly every agent's page, and /cma/[code] prints it as the page and
-- link-preview description. The report it leads to shows comparable sales and
-- the range they support; it does not estimate what a home is worth.
--
-- Jerry, 2026-11-11: the new wording is 'See what homes like yours have sold
-- for.', applied ONLY where the stored value still exactly matches the 0039
-- default. An agent who edited their description keeps it; NULL stays NULL
-- (the API supplies its own fallback). Only the column default and that one
-- exact value change. The headline's 0039 default is not touched.
--
-- Read-only count before applying (the runbook in the PR):
--   SELECT count(*) FROM users
--   WHERE landing_page_subheadline = 'Find out what your home is worth in today''s market.';

SET LOCAL lock_timeout = '5s';

ALTER TABLE users
  ALTER COLUMN landing_page_subheadline
  SET DEFAULT 'See what homes like yours have sold for.';

UPDATE users
SET landing_page_subheadline = 'See what homes like yours have sold for.'
WHERE landing_page_subheadline = 'Find out what your home is worth in today''s market.';
