-- ============================================================
-- vw_behavior
-- Purpose : Per-page user engagement metrics joined with scroll-depth
--           data aggregated from fct_events.
-- Sources : fct_sessions JOIN dim_dates JOIN dim_pages
--           LEFT JOIN fct_events (scroll events only)
-- Key metrics:
--   sessions              — distinct session count per page per day
--   pageviews             — total pageviews for this page
--   avg_time_on_page_s    — mean session duration as proxy for time on page
--   exits                 — sessions that bounced on this page
--   exit_rate_pct         — exits / sessions * 100
--   avg_scroll_depth_pct  — mean scroll percentage from scroll events (0-100)
-- Usage : SELECT * FROM vw_behavior ORDER BY pageviews DESC LIMIT 20
-- ============================================================
CREATE OR REPLACE VIEW vw_behavior AS
SELECT
    d.full_date,
    p.url,
    p.url_path,
    p.page_title,
    p.page_section,
    s.device_category,
    COUNT(DISTINCT s.session_id)                AS sessions,
    SUM(s.pageviews)                            AS pageviews,
    ROUND(AVG(s.session_duration_s), 2)         AS avg_time_on_page_s,
    SUM(CASE WHEN s.bounced THEN 1 ELSE 0 END)  AS exits,
    ROUND(
        100.0 * SUM(CASE WHEN s.bounced THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2
    )                                           AS exit_rate_pct,
    -- scroll depth from events
    ROUND(
        AVG(e.avg_scroll_pct), 2
    )                                           AS avg_scroll_depth_pct
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
JOIN dim_pages p  ON s.page_id = p.page_id
LEFT JOIN (
    SELECT page_id, AVG(scroll_depth_pct) AS avg_scroll_pct
    FROM fct_events
    WHERE event_name = 'scroll'
    GROUP BY page_id
) e ON e.page_id = s.page_id
GROUP BY 1,2,3,4,5,6;


CREATE OR REPLACE VIEW vw_funnel AS
-- Generic funnel: landing → any engagement event → conversion
SELECT
    d.full_date,
    COUNT(DISTINCT s.session_id)                            AS step1_landed,
    COUNT(DISTINCT CASE WHEN ev.has_engagement THEN s.session_id END)  AS step2_engaged,
    COUNT(DISTINCT CASE WHEN s.conversions > 0 THEN s.session_id END)  AS step3_converted
FROM fct_sessions s
JOIN dim_dates d ON s.date_id = d.date_id
LEFT JOIN (
    SELECT DISTINCT session_id, TRUE AS has_engagement
    FROM fct_events
    WHERE event_name IN ('click', 'scroll', 'form_submit', 'add_to_cart')
) ev ON ev.session_id = s.session_id
GROUP BY 1;
