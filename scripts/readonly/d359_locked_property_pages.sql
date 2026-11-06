-- D-359: how many production property pages have an access code stored?
-- READ ONLY. Runs inside a read-only transaction and ends with ROLLBACK; it writes nothing.
-- It never selects the codes themselves.
--
-- Before the D-359 fix, any non-NULL, non-empty access_code locked the page: the public
-- endpoint returned requires_access_code = bool(access_code), no visitor could enter the
-- code, and the lead route refused every lead without it. After the fix the codes stay in
-- the database but are ignored, so this counts the pages that WERE locked until the fix
-- deployed, and what that cost. "Locked" below matches the old API exactly (a value of
-- only spaces counts too).

BEGIN TRANSACTION READ ONLY;

-- 1. The count, and what it cost. The public endpoint bumps view_count BEFORE the access
--    check, so on a locked page every recorded view was a visitor who hit the lock.
SELECT
  count(*) FILTER (WHERE access_code IS NOT NULL AND access_code <> '')                AS locked_pages,
  count(*) FILTER (WHERE access_code IS NOT NULL AND access_code <> '' AND is_active)  AS locked_and_active,
  count(DISTINCT account_id) FILTER (WHERE access_code IS NOT NULL AND access_code <> '') AS accounts_with_a_locked_page,
  coalesce(sum(view_count) FILTER (WHERE access_code IS NOT NULL AND access_code <> ''), 0) AS views_on_locked_pages,
  max(last_viewed_at) FILTER (WHERE access_code IS NOT NULL AND access_code <> '')      AS last_view_on_a_locked_page,
  count(*)                                                                               AS all_property_pages
FROM property_reports;

-- 2. Which accounts, so you can decide whether anyone needs telling. Names and counts only.
SELECT a.name AS account, count(*) AS locked_pages, coalesce(sum(pr.view_count), 0) AS views_turned_away,
       max(pr.last_viewed_at) AS last_view
FROM property_reports pr
JOIN accounts a ON a.id = pr.account_id
WHERE pr.access_code IS NOT NULL AND pr.access_code <> ''
GROUP BY a.name
ORDER BY locked_pages DESC;

ROLLBACK;
