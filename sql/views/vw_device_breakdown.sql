-- vw_device_breakdown: sessions by device category with bounce rate, duration, and share pct.
CREATE OR REPLACE VIEW vw_device_breakdown AS
WITH device_totals AS (
    SELECT
        device_category,
        SUM(sessions)                                                AS total_sessions,
        SUM(new_users)                                               AS total_new_users,
        SUM(pageviews)                                               AS total_pageviews,
        ROUND(AVG(session_duration_s)::numeric, 2)                   AS avg_session_duration,
        ROUND(
            100.0 * SUM(CASE WHEN bounce THEN sessions ELSE 0 END)
            / NULLIF(SUM(sessions), 0), 2
        )                                                            AS bounce_rate_pct
    FROM raw_ga4_sessions
    WHERE device_category IS NOT NULL
    GROUP BY device_category
),
grand_total AS (
    SELECT SUM(total_sessions) AS grand_sessions FROM device_totals
)
SELECT
    d.device_category,
    d.total_sessions,
    d.total_new_users,
    d.total_pageviews,
    d.avg_session_duration,
    d.bounce_rate_pct,
    ROUND(100.0 * d.total_sessions / NULLIF(g.grand_sessions, 0), 2) AS device_share_pct
FROM device_totals d
CROSS JOIN grand_total g
ORDER BY d.total_sessions DESC;
