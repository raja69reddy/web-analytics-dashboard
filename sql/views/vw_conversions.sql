DROP VIEW IF EXISTS vw_conversions CASCADE;
-- vw_conversions: daily conversion metrics by channel/source/medium from raw_ga4_sessions.
-- Synthetic CVR per channel: Email 6.5%, Paid Search 4.8%, Organic 3.2%, Direct 2.8%, Social 1.8%.
-- Revenue = goal_completions * $52 avg order value.
CREATE OR REPLACE VIEW vw_conversions AS
WITH channel_rates AS (
    SELECT channel_grouping,
           CASE
               WHEN channel_grouping = 'Email'          THEN 0.065
               WHEN channel_grouping = 'Paid Search'    THEN 0.048
               WHEN channel_grouping = 'Organic Search' THEN 0.032
               WHEN channel_grouping = 'Direct'         THEN 0.028
               WHEN channel_grouping = 'Referral'       THEN 0.022
               WHEN channel_grouping = 'Social'         THEN 0.018
               ELSE 0.025
           END AS conv_rate
    FROM (SELECT DISTINCT channel_grouping FROM raw_ga4_sessions) c
),
session_data AS (
    SELECT
        g.session_date,
        g.channel_grouping,
        g.source,
        g.medium,
        SUM(g.sessions)                                                    AS sessions,
        SUM(g.new_users)                                                   AS new_users,
        SUM(g.pageviews)                                                   AS pageviews,
        SUM(CASE WHEN g.bounce = FALSE THEN g.sessions ELSE 0 END)        AS engaged_sessions,
        cr.conv_rate
    FROM raw_ga4_sessions g
    JOIN channel_rates cr ON cr.channel_grouping = g.channel_grouping
    GROUP BY g.session_date, g.channel_grouping, g.source, g.medium, cr.conv_rate
)
SELECT
    session_date,
    channel_grouping,
    source,
    medium,
    sessions,
    new_users,
    pageviews,
    engaged_sessions,
    (sessions * conv_rate)::int                          AS goal_completions,
    ROUND((sessions * conv_rate * 52.0)::numeric, 2)     AS revenue,
    ROUND((conv_rate * 100.0)::numeric, 4)               AS conversion_rate_pct,
    52.0::numeric                                        AS revenue_per_conversion
FROM session_data
ORDER BY session_date DESC, goal_completions DESC;
