-- vw_daily_traffic: daily sessions totals with 7-day rolling average.
CREATE OR REPLACE VIEW vw_daily_traffic AS
WITH daily AS (
    SELECT
        session_date,
        SUM(sessions)                                                AS total_sessions,
        SUM(new_users)                                               AS new_users,
        SUM(pageviews)                                               AS total_pageviews,
        ROUND(
            100.0 * SUM(CASE WHEN bounce THEN sessions ELSE 0 END)
            / NULLIF(SUM(sessions), 0), 2
        )                                                            AS bounce_rate_pct,
        ROUND(AVG(session_duration_s)::numeric, 2)                   AS avg_session_duration
    FROM raw_ga4_sessions
    GROUP BY session_date
)
SELECT
    session_date,
    total_sessions,
    new_users,
    total_pageviews,
    bounce_rate_pct,
    avg_session_duration,
    ROUND(
        AVG(total_sessions) OVER (
            ORDER BY session_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric, 2
    ) AS sessions_7day_avg
FROM daily
ORDER BY session_date;
