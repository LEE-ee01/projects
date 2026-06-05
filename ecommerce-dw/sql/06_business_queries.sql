-- ============================================================
-- ShopEasy 电商数据仓库
-- 06: 业务分析查询
-- 说明：15 个常见数据分析场景的 SQL 查询示例
--       覆盖：趋势分析、对比分析、排名分析、分层分析、漏斗分析
-- ============================================================

-- ----------------------------------------------------------
-- BQ1: 2025年各月 GMV 趋势
-- ----------------------------------------------------------
SELECT
    order_month,
    gmv,
    order_count,
    unique_buyers,
    aov,
    gmv_mom
FROM ads.ads_monthly_summary
WHERE order_month >= '2025-01-01'
ORDER BY order_month;

-- ----------------------------------------------------------
-- BQ2: 双11前后每日 GMV 对比（2025年11月1日-11月30日）
-- ----------------------------------------------------------
SELECT
    order_date,
    gmv,
    order_count,
    unique_buyers,
    aov
FROM ads.ads_daily_kpi
WHERE order_date BETWEEN '2025-11-01' AND '2025-11-30'
ORDER BY order_date;

-- ----------------------------------------------------------
-- BQ3: Top 10 品类排名（最近一个月）
-- ----------------------------------------------------------
SELECT
    category_l1,
    category_l2,
    revenue,
    order_count,
    unique_buyers,
    revenue_rank,
    revenue_share
FROM ads.ads_category_ranking
WHERE order_month = (SELECT MAX(order_month) FROM ads.ads_category_ranking)
ORDER BY revenue_rank
LIMIT 10;

-- ----------------------------------------------------------
-- BQ4: Top 10 城市业绩（累计）
-- ----------------------------------------------------------
SELECT
    city,
    SUM(revenue)    AS total_revenue,
    SUM(order_count) AS total_orders,
    SUM(unique_buyers) AS total_buyers,
    ROUND(AVG(avg_aov), 2) AS avg_aov
FROM ads.ads_city_performance
GROUP BY city
ORDER BY total_revenue DESC
LIMIT 10;

-- ----------------------------------------------------------
-- BQ5: 会员等级 ARPU 对比
-- ----------------------------------------------------------
SELECT
    membership_level,
    ROUND(AVG(arpu), 2)                     AS avg_arpu,
    ROUND(AVG(avg_order_value), 2)          AS avg_aov,
    ROUND(AVG(avg_discount_rate) * 100, 2)  AS avg_discount_pct,
    SUM(total_revenue)                      AS total_revenue,
    SUM(unique_buyers)                      AS total_buyers
FROM ads.ads_membership_analysis
GROUP BY membership_level
ORDER BY avg_arpu DESC;

-- ----------------------------------------------------------
-- BQ6: 用户首购到复购的平均间隔
-- ----------------------------------------------------------
WITH user_purchases AS (
    SELECT
        user_id,
        order_date,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) AS purchase_seq
    FROM dwd.dwd_orders
    WHERE order_valid_flag = '有效'
),
first_second AS (
    SELECT
        f.user_id,
        f.order_date AS first_purchase,
        s.order_date AS second_purchase,
        DATEDIFF('day', f.order_date, s.order_date) AS days_between
    FROM user_purchases f
    JOIN user_purchases s ON f.user_id = s.user_id AND f.purchase_seq = 1 AND s.purchase_seq = 2
)
SELECT
    COUNT(*)                                AS users_with_repurchase,
    ROUND(AVG(days_between), 1)             AS avg_days_to_repurchase,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_between), 1) AS median_days_to_repurchase
FROM first_second;

-- ----------------------------------------------------------
-- BQ7: 周末 vs 工作日消费对比
-- ----------------------------------------------------------
SELECT
    is_weekend,
    COUNT(DISTINCT order_id)        AS order_count,
    SUM(actual_amount)              AS total_revenue,
    ROUND(AVG(actual_amount), 2)    AS avg_order_value,
    COUNT(DISTINCT user_id)         AS unique_buyers
FROM dwd.dwd_orders
WHERE order_valid_flag = '有效'
GROUP BY is_weekend;

-- ----------------------------------------------------------
-- BQ8: 各时段销售额占比
-- ----------------------------------------------------------
SELECT
    time_period,
    SUM(order_count)                                        AS total_orders,
    SUM(revenue)                                            AS total_revenue,
    ROUND(SUM(revenue) * 1.0 / SUM(SUM(revenue)) OVER(), 4) AS revenue_share
FROM ads.ads_hourly_traffic
GROUP BY time_period
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------
-- BQ9: 折扣力度与购买转化关系
-- ----------------------------------------------------------
SELECT
    discount_bucket,
    SUM(order_count)       AS total_orders,
    SUM(unique_buyers)     AS total_buyers,
    ROUND(AVG(avg_order_value), 2) AS avg_aov
FROM ads.ads_discount_effectiveness
GROUP BY discount_bucket
ORDER BY discount_bucket;

-- ----------------------------------------------------------
-- BQ10: 用户 RFM 分层占比
-- ----------------------------------------------------------
SELECT
    rfm_segment,
    COUNT(*)                                        AS user_count,
    ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER(), 4) AS user_share,
    ROUND(AVG(monetary), 2)                         AS avg_ltv,
    ROUND(AVG(frequency), 1)                        AS avg_purchase_count
FROM ads.ads_user_rfm
GROUP BY rfm_segment
ORDER BY user_count DESC;

-- ----------------------------------------------------------
-- BQ11: 月度新客 vs 老客贡献
-- ----------------------------------------------------------
WITH user_first_purchase AS (
    SELECT
        user_id,
        MIN(order_date) AS first_purchase_date
    FROM dwd.dwd_orders
    WHERE order_valid_flag = '有效'
    GROUP BY user_id
)
SELECT
    DATE_TRUNC('month', o.order_date) AS order_month,
    CASE WHEN o.order_date = ufp.first_purchase_date THEN '新客' ELSE '老客' END AS customer_type,
    COUNT(DISTINCT o.user_id)         AS buyer_count,
    SUM(o.actual_amount)              AS revenue
FROM dwd.dwd_orders o
JOIN user_first_purchase ufp ON o.user_id = ufp.user_id
WHERE o.order_valid_flag = '有效'
GROUP BY order_month, customer_type
ORDER BY order_month, customer_type;

-- ----------------------------------------------------------
-- BQ12: 高价值商品（单价>1000）销售趋势
-- ----------------------------------------------------------
SELECT
    DATE_TRUNC('month', o.order_date) AS order_month,
    COUNT(DISTINCT o.order_id)        AS order_count,
    SUM(o.actual_amount)              AS revenue,
    COUNT(DISTINCT o.user_id)         AS buyers
FROM dwd.dwd_orders o
JOIN dwd.dwd_products p ON o.product_id = p.product_id
WHERE o.order_valid_flag = '有效'
  AND p.price_range IN ('1000-5000元', '5000元以上')
GROUP BY order_month
ORDER BY order_month;

-- ----------------------------------------------------------
-- BQ13: 各城市层级 GMV 对比
-- ----------------------------------------------------------
WITH city_tier AS (
    SELECT city,
        CASE
            WHEN city IN ('北京', '上海', '广州', '深圳') THEN '一线城市'
            WHEN city IN ('杭州', '成都', '武汉', '南京', '重庆', '西安', '长沙', '苏州', '天津', '郑州') THEN '二线城市'
            ELSE '三线城市'
        END AS city_tier
    FROM ads.ads_city_performance
    GROUP BY city
)
SELECT
    ct.city_tier,
    SUM(cp.revenue)     AS total_revenue,
    SUM(cp.order_count) AS total_orders,
    SUM(cp.unique_buyers) AS total_buyers,
    ROUND(AVG(cp.avg_aov), 2) AS avg_aov
FROM ads.ads_city_performance cp
JOIN city_tier ct ON cp.city = ct.city
GROUP BY ct.city_tier
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------
-- BQ14: 毛利率最高的 10 个二级品类
-- ----------------------------------------------------------
SELECT
    category_l1,
    category_l2,
    ROUND(AVG(gross_margin) * 100, 1) AS avg_gross_margin_pct,
    COUNT(*)                           AS product_count,
    ROUND(AVG(unit_price), 2)          AS avg_price
FROM dwd.dwd_products
GROUP BY category_l1, category_l2
ORDER BY avg_gross_margin_pct DESC
LIMIT 10;

-- ----------------------------------------------------------
-- BQ15: 2025年各月 GMV 同比（带12个月前的对比）
-- ----------------------------------------------------------
SELECT
    order_month,
    gmv,
    LAG(gmv, 12) OVER (ORDER BY order_month) AS gmv_last_year,
    ROUND((gmv - LAG(gmv, 12) OVER (ORDER BY order_month))
          / NULLIF(LAG(gmv, 12) OVER (ORDER BY order_month), 0) * 100, 1) AS gmv_yoy_pct
FROM ads.ads_monthly_summary
WHERE order_month >= '2024-01-01'
ORDER BY order_month;
