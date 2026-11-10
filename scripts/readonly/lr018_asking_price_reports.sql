-- LR-018 / D-377: how many stored reports counted an asking price as a sale?
-- READ ONLY. Runs inside a read-only transaction and ends with ROLLBACK; it writes nothing.
-- It selects no addresses, names, phone numbers or email addresses: counts and dates only.
--
-- The defect: when the MLS listing had no close price, every comp builder fell back to
-- listPrice, and a missing MLS status defaulted to "Closed". The range, median and $/sqft
-- then treated that asking price as a recorded sale.
--
-- What each stored shape can tell us (one verdict per comp):
--   consumer_reports.comparables (homeowner /r report and its PDF) carry `price`,
--     `list_price`, `close_price` and `status`.
--       definite       counted as closed, no close_price, a positive price: an asking price
--                      shown as a sale.
--   property_reports.comparables (agent PDF) carry the wizard's `sale_price`, already
--     collapsed as close_price || price || list_price, plus list_price; no close_price.
--       possible       counted as closed and sale_price = list_price. EITHER an asking price
--                      shown as a sale OR a genuine sale at exactly the asking price; the
--                      stored row cannot tell them apart, with or without a sold date.
--                      Never call these confirmed.
--   Either shape:
--       unknown: no status            no status recorded; cannot say whether it was a sale.
--       unknown: no list price        a sale with nothing to compare its price against.
--       unknown: legacy sold_price    an older row carrying only `sold_price`.
--       recorded sale / not a sale / no price   not affected.
--
-- Query 1 counts by verdict. A report with several kinds of comp appears under several
-- verdicts, so its rows CANNOT BE ADDED. Query 2 counts each report once, under its worst
-- verdict (definite > possible > unknown), and its rows can be added.
-- Queries 1 and 2 repeat the same classification (a read-only transaction cannot create a
-- view); tests/test_lr018_readonly_count_classifies_comps.py checks the two copies match.
--
-- Owner decision (DECISIONS_AND_LANES.md): run this count first. No rerender, no notice.

BEGIN TRANSACTION READ ONLY;

-- 1. By table, report status and verdict. Overlapping: do not add rows.
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
           nullif(lower(trim(coalesce(c->>'status', ''))), '')                   AS status,
           CASE WHEN c->>'price'       ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'price')::numeric       END AS price,
           CASE WHEN c->>'close_price' ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'close_price')::numeric END AS close_price,
           CASE WHEN c->>'sale_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'sale_price')::numeric  END AS sale_price,
           CASE WHEN c->>'sold_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'sold_price')::numeric  END AS sold_price,
           CASE WHEN c->>'list_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'list_price')::numeric  END AS list_price,
           coalesce(nullif(c->>'close_date', ''), nullif(c->>'sold_date', '')) IS NOT NULL AS has_sale_date,
           c ? 'close_price' AS has_close_field
    FROM comps
),
judged AS (
    SELECT source, id, report_status, created_at, has_sale_date,
           CASE
             WHEN status IS NULL                                             THEN 'unknown: no status'
             WHEN status NOT IN ('closed', 'sold')                           THEN 'not a sale'
             -- consumer / API shape: close_price is the record of the sale
             WHEN has_close_field AND coalesce(close_price, 0) > 0            THEN 'recorded sale'
             WHEN has_close_field AND coalesce(price, 0) > 0                  THEN 'definite'
             WHEN has_close_field                                            THEN 'no price'
             -- wizard / legacy shape: only sale_price (or price) and list_price survive
             WHEN sale_price IS NULL AND price IS NULL AND sold_price IS NOT NULL
                                                                             THEN 'unknown: legacy sold_price'
             WHEN coalesce(sale_price, price, 0) <= 0                         THEN 'no price'
             WHEN list_price IS NULL                                         THEN 'unknown: no list price'
             WHEN coalesce(sale_price, price) = list_price                   THEN 'possible'
             ELSE 'recorded sale'
           END AS verdict
    FROM num
)
SELECT source, report_status, verdict,
       count(DISTINCT id)                         AS reports,
       count(*)                                   AS comps,
       count(*) FILTER (WHERE NOT has_sale_date)  AS comps_without_sale_date,
       min(created_at)                            AS oldest,
       max(created_at)                            AS newest
FROM judged
WHERE verdict IN ('definite', 'possible', 'unknown: no status',
                  'unknown: no list price', 'unknown: legacy sold_price')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;

-- 2. Each report once, under its worst verdict. These rows CAN be added.
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
           nullif(lower(trim(coalesce(c->>'status', ''))), '')                   AS status,
           CASE WHEN c->>'price'       ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'price')::numeric       END AS price,
           CASE WHEN c->>'close_price' ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'close_price')::numeric END AS close_price,
           CASE WHEN c->>'sale_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'sale_price')::numeric  END AS sale_price,
           CASE WHEN c->>'sold_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'sold_price')::numeric  END AS sold_price,
           CASE WHEN c->>'list_price'  ~ '^[0-9]+(\.[0-9]+)?$' THEN (c->>'list_price')::numeric  END AS list_price,
           coalesce(nullif(c->>'close_date', ''), nullif(c->>'sold_date', '')) IS NOT NULL AS has_sale_date,
           c ? 'close_price' AS has_close_field
    FROM comps
),
judged AS (
    SELECT source, id, report_status, created_at, has_sale_date,
           CASE
             WHEN status IS NULL                                             THEN 'unknown: no status'
             WHEN status NOT IN ('closed', 'sold')                           THEN 'not a sale'
             -- consumer / API shape: close_price is the record of the sale
             WHEN has_close_field AND coalesce(close_price, 0) > 0            THEN 'recorded sale'
             WHEN has_close_field AND coalesce(price, 0) > 0                  THEN 'definite'
             WHEN has_close_field                                            THEN 'no price'
             -- wizard / legacy shape: only sale_price (or price) and list_price survive
             WHEN sale_price IS NULL AND price IS NULL AND sold_price IS NOT NULL
                                                                             THEN 'unknown: legacy sold_price'
             WHEN coalesce(sale_price, price, 0) <= 0                         THEN 'no price'
             WHEN list_price IS NULL                                         THEN 'unknown: no list price'
             WHEN coalesce(sale_price, price) = list_price                   THEN 'possible'
             ELSE 'recorded sale'
           END AS verdict
    FROM num
),
worst AS (
    SELECT source, id, report_status,
           min(CASE verdict WHEN 'definite' THEN 1 WHEN 'possible' THEN 2
                            WHEN 'unknown: no status' THEN 3
                            WHEN 'unknown: no list price' THEN 3
                            WHEN 'unknown: legacy sold_price' THEN 3
                            ELSE 4 END) AS rank
    FROM judged
    GROUP BY 1, 2, 3
)
SELECT source, report_status,
       CASE rank WHEN 1 THEN 'definite' WHEN 2 THEN 'possible'
                 WHEN 3 THEN 'unknown' ELSE 'clean' END AS worst_verdict,
       count(*) AS reports
FROM worst
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;

-- 3. For scale: every report and comp in each table.
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
