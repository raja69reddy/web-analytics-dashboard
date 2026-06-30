-- vw_engagement_events: event type breakdown per page from clickstream data.
CREATE OR REPLACE VIEW vw_engagement_events AS
SELECT
    page_url,
    COUNT(*)                                                       AS total_events,
    COUNT(CASE WHEN event_name = 'click'       THEN 1 END)        AS click_events,
    COUNT(CASE WHEN event_name = 'scroll'      THEN 1 END)        AS scroll_events,
    COUNT(CASE WHEN event_name = 'pageview'    THEN 1 END)        AS pageview_events,
    COUNT(CASE WHEN event_name = 'form_submit' THEN 1 END)        AS form_submit_events,
    COUNT(DISTINCT session_id)                                     AS unique_sessions,
    COUNT(DISTINCT user_pseudo_id)                                 AS unique_users,
    ROUND(
        100.0 * COUNT(CASE WHEN event_name IN ('click', 'form_submit') THEN 1 END)
        / NULLIF(COUNT(*), 0), 2
    )                                                              AS interaction_rate_pct,
    ROUND(
        COUNT(*)::numeric / NULLIF(COUNT(DISTINCT session_id), 0), 2
    )                                                              AS events_per_session
FROM raw_clickstream_events
GROUP BY page_url
ORDER BY total_events DESC;
