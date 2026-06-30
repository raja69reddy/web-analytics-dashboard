-- vw_error_pages: 4xx and 5xx errors per page with trend over time.
CREATE OR REPLACE VIEW vw_error_pages AS
WITH error_by_page AS (
    SELECT
        url,
        COUNT(*)                                                      AS total_requests,
        COUNT(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 END)  AS errors_4xx,
        COUNT(CASE WHEN status_code BETWEEN 500 AND 599 THEN 1 END)  AS errors_5xx,
        COUNT(CASE WHEN status_code >= 400              THEN 1 END)  AS total_errors,
        MIN(log_time)                                                 AS first_error,
        MAX(log_time)                                                 AS last_error
    FROM raw_server_logs
    GROUP BY url
),
error_by_day AS (
    SELECT
        url,
        log_time::date                                                AS error_date,
        COUNT(CASE WHEN status_code >= 400 THEN 1 END)               AS daily_errors
    FROM raw_server_logs
    GROUP BY url, log_time::date
)
SELECT
    e.url,
    e.total_requests,
    e.errors_4xx,
    e.errors_5xx,
    e.total_errors,
    ROUND(100.0 * e.total_errors / NULLIF(e.total_requests, 0), 2)   AS error_rate_pct,
    e.first_error,
    e.last_error
FROM error_by_page e
WHERE e.total_errors > 0
ORDER BY e.total_errors DESC
LIMIT 10;
