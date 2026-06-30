-- top_pages.sql: top 20 pages by pageviews for a given date range (:start_date, :end_date).

SELECT
    p.url,
    p.url_path,
    p.page_title,
    p.page_section,
    SUM(s.pageviews)                                    AS total_pageviews,
    COUNT(DISTINCT s.session_id)                        AS unique_sessions,
    ROUND(AVG(s.session_duration_s), 2)                 AS avg_time_on_page_s,
    SUM(CASE WHEN s.bounced THEN 1 ELSE 0 END)          AS bounces,
    ROUND(
        100.0 * SUM(CASE WHEN s.bounced THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2
    )                                                   AS bounce_rate_pct
FROM fct_sessions s
JOIN dim_pages p  ON s.page_id = p.page_id
JOIN dim_dates d  ON s.date_id = d.date_id
WHERE d.full_date BETWEEN :start_date AND :end_date
GROUP BY p.url, p.url_path, p.page_title, p.page_section
ORDER BY total_pageviews DESC
LIMIT 20;
