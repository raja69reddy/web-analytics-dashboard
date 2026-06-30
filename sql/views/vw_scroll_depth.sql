-- vw_scroll_depth: average scroll depth per page with distribution buckets (0-100 pct scale).
CREATE OR REPLACE VIEW vw_scroll_depth AS
WITH scroll_events AS (
    SELECT
        page_url,
        scroll_depth_pct
    FROM raw_clickstream_events
    WHERE event_name = 'scroll'
      AND scroll_depth_pct IS NOT NULL
),
page_scroll AS (
    SELECT
        page_url,
        COUNT(*)                                                         AS scroll_events,
        ROUND(AVG(scroll_depth_pct)::numeric, 1)                        AS avg_scroll_depth_pct,
        ROUND(MIN(scroll_depth_pct)::numeric, 1)                        AS min_scroll_depth_pct,
        ROUND(MAX(scroll_depth_pct)::numeric, 1)                        AS max_scroll_depth_pct,
        COUNT(CASE WHEN scroll_depth_pct <= 25                THEN 1 END) AS bucket_0_25,
        COUNT(CASE WHEN scroll_depth_pct > 25  AND scroll_depth_pct <= 50  THEN 1 END) AS bucket_25_50,
        COUNT(CASE WHEN scroll_depth_pct > 50  AND scroll_depth_pct <= 75  THEN 1 END) AS bucket_50_75,
        COUNT(CASE WHEN scroll_depth_pct > 75                THEN 1 END) AS bucket_75_100
    FROM scroll_events
    GROUP BY page_url
)
SELECT
    page_url,
    scroll_events,
    avg_scroll_depth_pct,
    min_scroll_depth_pct,
    max_scroll_depth_pct,
    bucket_0_25,
    bucket_25_50,
    bucket_50_75,
    bucket_75_100,
    ROUND(100.0 * bucket_0_25    / NULLIF(scroll_events, 0), 1) AS pct_0_25,
    ROUND(100.0 * bucket_25_50   / NULLIF(scroll_events, 0), 1) AS pct_25_50,
    ROUND(100.0 * bucket_50_75   / NULLIF(scroll_events, 0), 1) AS pct_50_75,
    ROUND(100.0 * bucket_75_100  / NULLIF(scroll_events, 0), 1) AS pct_75_100
FROM page_scroll
ORDER BY avg_scroll_depth_pct DESC;
