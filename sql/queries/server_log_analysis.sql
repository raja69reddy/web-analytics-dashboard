-- server_log_analysis.sql
-- Four reusable analysis queries against raw_server_logs.
-- Run individually by copying the desired block into psql or query_df().

-- ── Query 1: Requests per hour of day ────────────────────────────────────
-- Shows the hour-of-day distribution of traffic to identify peak times.
SELECT
    EXTRACT(HOUR FROM log_time)::int   AS hour_of_day,
    COUNT(*)                           AS request_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM raw_server_logs
GROUP BY hour_of_day
ORDER BY hour_of_day;


-- ── Query 2: Top 10 pages by request count ───────────────────────────────
-- Identifies the most frequently accessed URLs.
SELECT
    url,
    COUNT(*)                           AS request_count,
    COUNT(CASE WHEN status_code = 200 THEN 1 END) AS ok_count,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) AS error_count,
    ROUND(
        100.0 * COUNT(CASE WHEN status_code >= 400 THEN 1 END)
        / NULLIF(COUNT(*), 0), 2
    )                                  AS error_rate_pct
FROM raw_server_logs
GROUP BY url
ORDER BY request_count DESC
LIMIT 10;


-- ── Query 3: Error rate by day (4xx + 5xx / total) ───────────────────────
-- Tracks error rate over time to surface degraded days.
SELECT
    log_time::date                     AS log_date,
    COUNT(*)                           AS total_requests,
    COUNT(CASE WHEN status_code BETWEEN 400 AND 599 THEN 1 END) AS error_count,
    ROUND(
        100.0 * COUNT(CASE WHEN status_code BETWEEN 400 AND 599 THEN 1 END)
        / NULLIF(COUNT(*), 0), 2
    )                                  AS error_rate_pct
FROM raw_server_logs
GROUP BY log_date
ORDER BY log_date;


-- ── Query 4: Average response time by page ───────────────────────────────
-- Highlights slow pages that may need performance attention.
SELECT
    url,
    COUNT(*)                           AS request_count,
    ROUND(AVG(response_time_ms), 0)    AS avg_response_ms,
    ROUND(MIN(response_time_ms), 0)    AS min_response_ms,
    ROUND(MAX(response_time_ms), 0)    AS max_response_ms,
    ROUND(
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms), 0
    )                                  AS p95_response_ms
FROM raw_server_logs
WHERE response_time_ms IS NOT NULL
GROUP BY url
ORDER BY avg_response_ms DESC;
