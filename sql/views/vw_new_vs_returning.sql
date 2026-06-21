-- vw_new_vs_returning: new vs returning user sessions by date.
CREATE OR REPLACE VIEW vw_new_vs_returning AS
SELECT
    session_date,
    SUM(sessions)                                                    AS total_sessions,
    SUM(new_users)                                                   AS new_user_sessions,
    SUM(sessions) - SUM(new_users)                                   AS returning_user_sessions,
    ROUND(100.0 * SUM(new_users) / NULLIF(SUM(sessions), 0), 2)     AS new_user_pct,
    ROUND(
        100.0 * (SUM(sessions) - SUM(new_users)) / NULLIF(SUM(sessions), 0), 2
    )                                                                AS returning_user_pct
FROM raw_ga4_sessions
GROUP BY session_date
ORDER BY session_date;
