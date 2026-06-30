-- channel_breakdown.sql
-- Returns traffic and conversion metrics aggregated by channel grouping.
-- Useful for the channel breakdown bar chart on the Traffic dashboard page.
-- Parameters (optional — remove WHERE clause to get all-time totals):
--   :start_date  DATE  e.g. '2024-01-01'
--   :end_date    DATE  e.g. '2024-03-31'
--
-- Example usage in Python:
--   query_sql_file('sql/queries/channel_breakdown.sql', {'start_date': '2024-01-01', 'end_date': '2024-03-31'})

SELECT
    s.channel_grouping,
    COUNT(*)                                                AS sessions,
    SUM(CASE WHEN s.is_new_user THEN 1 ELSE 0 END)         AS new_users,
    SUM(s.pageviews)                                        AS pageviews,
    SUM(CASE WHEN s.bounced THEN 1 ELSE 0 END)              AS bounces,
    ROUND(
        100.0 * SUM(CASE WHEN s.bounced THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2
    )                                                       AS bounce_rate_pct,
    ROUND(AVG(s.session_duration_s), 2)                     AS avg_session_duration_s,
    SUM(s.conversions)                                      AS conversions,
    ROUND(
        100.0 * SUM(CASE WHEN s.conversions > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 4
    )                                                       AS conversion_rate_pct,
    SUM(s.revenue)                                          AS revenue
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
WHERE d.full_date BETWEEN :start_date AND :end_date
GROUP BY s.channel_grouping
ORDER BY sessions DESC;
