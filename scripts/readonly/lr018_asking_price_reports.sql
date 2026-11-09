-- LR-018 / D-377: how many stored reports counted an asking price as a sale?
-- READ ONLY. Runs inside a read-only transaction and ends with ROLLBACK; it writes nothing.
-- It selects no addresses, names, phone numbers or email addresses: counts and dates only.
--
-- The defect: when the MLS listing had no close price, every comp builder fell back to
-- listPrice, and a missing MLS status defaulted to "Closed". The range, median and $/sqft
-- then treated that asking price as a recorded sale.
--
-- What each table can tell us:
--   consumer_reports.comparables (homeowner /r report and its PDF): each comp stores
--     `price`, `list_price`, `close_price` and `status`. A comp counted as closed with no
--     close_price and a positive price is DEFINITELY an asking price shown as a sale.
--   property_reports.comparables (agent PDF): the wizard stores `sale_price`, already
--     collapsed as close_price || price || list_price, and no close_price. So a closed comp
--     whose sale_price equals its list_price is EITHER an asking price shown as a sale OR
--     a real sale at exactly the asking price. With no sold date as well, it is almost
--     certainly the fallback (`definite`); with a sold date it is ambiguous (`possible`).
--
-- Owner decision (DECISIONS_AND_LANES.md): run this count first. No rerender, no notice.

BEGIN TRANSACTION READ ONLY;

WITH comps AS (
    SELECT 'consumer_reports'::text AS source, r.id, r.status AS report_status, r.created_at, c
    FROM consumer_reports r,
         jsonb_array_elements(CASE WHEN jsonb_typeof(r.comparables) = 'array'
                                   THEN r.comparables ELSE '[]'::jsonb END) AS c
    UNION ALL
    SELECT 'property_reports', r.id, r.status, r.created_at, c
    FROM property_reports r,
         jsonb_array_elements(CASE WHEN jsonb_typeof(r.comparables) = 'array'
                                   THEN r.comparables ELSE '[]'::jsonb END) AS c
),
num AS (
    SELECT source, id, report_status, created_at,
           lower(trim(coalesce(c->>'status', ''))) IN ('closed', 'sold')           AS counted_closed,
           CASE WHEN c->>'price'       ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'price')::numeric       END AS price,
           CASE WHEN c->>'close_price' ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'close_price')::numeric END AS close_price,
           CASE WHEN c->>'sale_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'sale_price')::numeric  END AS sale_price,
           CASE WHEN c->>'list_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'list_price')::numeric  END AS list_price,
           coalesce(nullif(c->>'close_date', ''), nullif(c->>'sold_date', '')) IS NOT NULL AS has_sale_date,
           c ? 'close_price' AS has_close_field
    FROM comps
),
judged AS (
    SELECT source, id, report_status, created_at,
           CASE
             WHEN NOT counted_closed THEN 'not counted as a sale'
             -- consumer shape: close_price recorded or not
             WHEN has_close_field AND coalesce(close_price, 0) > 0 THEN 'recorded sale'
             WHEN has_close_field AND coalesce(price, 0) > 0       THEN 'definite'
             -- agent shape: only sale_price and list_price survive
             WHEN NOT has_close_field AND coalesce(sale_price, price, 0) > 0
                  AND list_price IS NOT NULL
                  AND coalesce(sale_price, price) = list_price
                  AND NOT has_sale_date                           THEN 'definite'
             WHEN NOT has_close_field AND coalesce(sale_price, price, 0) > 0
                  AND list_price IS NOT NULL
                  AND coalesce(sale_price, price) = list_price    THEN 'possible'
             WHEN coalesce(sale_price, price, 0) > 0              THEN 'recorded sale'
             ELSE 'no price'
           END AS verdict
    FROM num
)

-- 1. Reports with at least one asking price shown as a sale, by table, report status
--    and verdict. `possible` exists only for agent reports (see above).
SELECT source, report_status, verdict,
       count(DISTINCT id) AS reports,
       count(*)           AS comps,
       min(created_at)    AS oldest,
       max(created_at)    AS newest
FROM judged
WHERE verdict IN ('definite', 'possible')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;

-- 2. For scale: every report and comp in each table, by verdict.
WITH comps AS (
    SELECT 'consumer_reports'::text AS source, r.id, c
    FROM consumer_reports r,
         jsonb_array_elements(CASE WHEN jsonb_typeof(r.comparables) = 'array'
                                   THEN r.comparables ELSE '[]'::jsonb END) AS c
    UNION ALL
    SELECT 'property_reports', r.id, c
    FROM property_reports r,
         jsonb_array_elements(CASE WHEN jsonb_typeof(r.comparables) = 'array'
                                   THEN r.comparables ELSE '[]'::jsonb END) AS c
)
SELECT source,
       count(DISTINCT id)                                                         AS reports_with_comps,
       count(*)                                                                   AS comps,
       count(*) FILTER (WHERE lower(trim(coalesce(c->>'status', ''))) IN ('closed', 'sold')) AS comps_counted_closed,
       count(*) FILTER (WHERE nullif(trim(coalesce(c->>'status', '')), '') IS NULL) AS comps_with_no_status
FROM comps
GROUP BY 1
ORDER BY 1;

ROLLBACK;
