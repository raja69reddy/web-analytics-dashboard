-- vw_traffic: sessions by date/channel from GA4 raw data, with request counts from server logs.
CREATE OR REPLACE VIEW vw_traffic AS
WITH ga4_stats AS (
    -- Sessions, pageviews, and engagement metrics by date and channel from raw GA4 data
    SELECT
        session_date,
        channel_grouping,
        source,
        medium,
        SUM(sessions)                              AS sessions,
        SUM(new_users)                             AS new_users,
        SUM(pageviews)                             AS pageviews,
        ROUND(AVG(session_duration_s)::numeric, 2) AS avg_session_duration_s,
        SUM(CASE WHEN bounce THEN 1 ELSE 0 END)    AS bounces
    FROM raw_ga4_sessions
    GROUP BY session_date, channel_grouping, source, medium
),
log_by_date AS (
    -- Request count by URL from server logs, aggregated to the day level for joining
    SELECT
        log_time::date      AS log_date,
        COUNT(*)            AS total_requests,
        COUNT(DISTINCT url) AS unique_urls,
        COUNT(CASE WHEN status_code >= 400 THEN 1 END) AS error_requests
    FROM raw_server_logs
    GROUP BY log_time::date
)
SELECT
    g.session_date,
    g.channel_grouping,
    g.source,
    g.medium,
    g.sessions,
    g.new_users,
    g.pageviews,
    g.bounces,
    ROUND(100.0 * g.bounces / NULLIF(g.sessions, 0), 2) AS bounce_rate_pct,
    g.avg_session_duration_s,
    COALESCE(l.total_requests, 0)  AS server_requests,
    COALESCE(l.unique_urls,    0)  AS unique_urls,
    COALESCE(l.error_requests, 0)  AS server_errors
FROM ga4_stats g
LEFT JOIN log_by_date l ON l.log_date = g.session_date;
