"""
ShopEasy 电商数据仓库 - Step 4: ADS 层业务指标构建

功能：
  - 基于 DWS 和 DWD 层构建 10 张业务分析指标表
  - 面向具体业务场景：KPI监控、用户分析、商品分析、地域分析、RFM分层
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    load_config, get_db_connection,
    print_step_header, print_row_count, logger
)


def main():
    print_step_header("ADS 层业务指标构建")

    config = load_config()
    conn = get_db_connection(config)

    try:
        # 创建 ADS schema
        conn.execute("CREATE SCHEMA IF NOT EXISTS ads")
        logger.info("  ADS Schema 已就绪")

        # --------------------------------------------------
        # ADS-1: 每日经营核心 KPI
        # --------------------------------------------------
        logger.info("  构建 ADS-1: 每日经营核心 KPI...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_daily_kpi AS
            SELECT
                order_date,
                COUNT(DISTINCT order_id)                        AS order_count,
                COUNT(DISTINCT user_id)                          AS unique_buyers,
                SUM(actual_amount)                               AS gmv,
                ROUND(SUM(actual_amount) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS aov,
                ROUND(COUNT(DISTINCT order_id) * 1.0 / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS orders_per_user,
                SUM(discount)                                    AS total_discount,
                ROUND(SUM(discount) * 1.0 / NULLIF(SUM(order_amount), 0), 4) AS discount_ratio,
                SUM(quantity)                                    AS total_quantity_sold
            FROM dwd.dwd_orders
            WHERE order_valid_flag = '有效'
            GROUP BY order_date
        """)
        print_row_count(conn, "ads.ads_daily_kpi", "  ADS.每日KPI")

        # --------------------------------------------------
        # ADS-2: 用户留存分析（周度 Cohort）
        # --------------------------------------------------
        logger.info("  构建 ADS-2: 用户留存分析...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_user_cohort AS
            WITH user_cohorts AS (
                SELECT
                    user_id,
                    DATE_TRUNC('week', register_time) AS cohort_week
                FROM dwd.dwd_users
            ),
            user_orders AS (
                SELECT DISTINCT
                    o.user_id,
                    DATE_TRUNC('week', o.order_date) AS order_week
                FROM dwd.dwd_orders o
                WHERE o.order_valid_flag = '有效'
            )
            SELECT
                uc.cohort_week,
                DATEDIFF('week', uc.cohort_week, uo.order_week) AS week_number,
                COUNT(DISTINCT uc.user_id)                       AS cohort_size,
                COUNT(DISTINCT uo.user_id)                       AS active_users,
                ROUND(COUNT(DISTINCT uo.user_id) * 1.0 /
                      NULLIF(COUNT(DISTINCT uc.user_id), 0), 4)  AS retention_rate
            FROM user_cohorts uc
            LEFT JOIN user_orders uo
                ON uc.user_id = uo.user_id AND uo.order_week >= uc.cohort_week
            GROUP BY uc.cohort_week, week_number
            HAVING week_number >= 0 AND week_number <= 12
        """)
        print_row_count(conn, "ads.ads_user_cohort", "  ADS.用户留存")

        # --------------------------------------------------
        # ADS-3: 品类月度排名
        # --------------------------------------------------
        logger.info("  构建 ADS-3: 品类月度排名...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_category_ranking AS
            WITH monthly_category AS (
                SELECT
                    DATE_TRUNC('month', order_date) AS order_month,
                    category_l1,
                    category_l2,
                    SUM(total_revenue)               AS revenue,
                    SUM(order_count)                 AS order_count,
                    SUM(unique_buyers)               AS unique_buyers
                FROM dws.dws_daily_category_sales
                GROUP BY order_month, category_l1, category_l2
            )
            SELECT
                order_month,
                category_l1,
                category_l2,
                revenue,
                order_count,
                unique_buyers,
                ROW_NUMBER() OVER (PARTITION BY order_month ORDER BY revenue DESC) AS revenue_rank,
                ROUND(revenue * 1.0 / NULLIF(SUM(revenue) OVER (PARTITION BY order_month), 0), 4) AS revenue_share,
                ROUND((revenue - LAG(revenue) OVER (
                    PARTITION BY category_l1, category_l2 ORDER BY order_month))
                    / NULLIF(LAG(revenue) OVER (
                        PARTITION BY category_l1, category_l2 ORDER BY order_month), 0), 4) AS mom_growth
            FROM monthly_category
        """)
        print_row_count(conn, "ads.ads_category_ranking", "  ADS.品类排名")

        # --------------------------------------------------
        # ADS-4: 城市业绩表现
        # --------------------------------------------------
        logger.info("  构建 ADS-4: 城市业绩表现...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_city_performance AS
            WITH monthly_city AS (
                SELECT
                    DATE_TRUNC('month', order_date) AS order_month,
                    city,
                    SUM(total_revenue)              AS revenue,
                    SUM(order_count)                AS order_count,
                    SUM(unique_buyers)              AS unique_buyers,
                    ROUND(AVG(avg_order_value), 2)  AS avg_aov
                FROM dws.dws_daily_city_sales
                GROUP BY order_month, city
            )
            SELECT
                order_month,
                city,
                revenue,
                order_count,
                unique_buyers,
                avg_aov,
                ROW_NUMBER() OVER (PARTITION BY order_month ORDER BY revenue DESC) AS city_rank,
                ROUND((revenue - LAG(revenue) OVER (PARTITION BY city ORDER BY order_month))
                      / NULLIF(LAG(revenue) OVER (PARTITION BY city ORDER BY order_month), 0), 4) AS mom_growth
            FROM monthly_city
        """)
        print_row_count(conn, "ads.ads_city_performance", "  ADS.城市业绩")

        # --------------------------------------------------
        # ADS-5: 会员等级消费分析
        # --------------------------------------------------
        logger.info("  构建 ADS-5: 会员等级消费分析...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_membership_analysis AS
            SELECT
                DATE_TRUNC('month', o.order_date)   AS order_month,
                u.membership_level,
                COUNT(DISTINCT o.order_id)           AS order_count,
                COUNT(DISTINCT o.user_id)            AS unique_buyers,
                SUM(o.actual_amount)                 AS total_revenue,
                ROUND(AVG(o.actual_amount), 2)       AS avg_order_value,
                ROUND(SUM(o.actual_amount) * 1.0 / NULLIF(COUNT(DISTINCT o.user_id), 0), 2) AS arpu,
                ROUND(AVG(o.discount_rate), 4)       AS avg_discount_rate
            FROM dwd.dwd_orders o
            JOIN dwd.dwd_users u ON o.user_id = u.user_id
            WHERE o.order_valid_flag = '有效'
            GROUP BY DATE_TRUNC('month', o.order_date), u.membership_level
        """)
        print_row_count(conn, "ads.ads_membership_analysis", "  ADS.会员分析")

        # --------------------------------------------------
        # ADS-6: 时段流量分析
        # --------------------------------------------------
        logger.info("  构建 ADS-6: 时段流量分析...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_hourly_traffic AS
            SELECT
                CASE
                    WHEN order_hour >= 0  AND order_hour < 6  THEN '凌晨(00-06)'
                    WHEN order_hour >= 6  AND order_hour < 12 THEN '上午(06-12)'
                    WHEN order_hour >= 12 AND order_hour < 18 THEN '下午(12-18)'
                    WHEN order_hour >= 18 AND order_hour < 24 THEN '晚间(18-24)'
                END                                     AS time_period,
                order_hour,
                order_dow                               AS day_of_week,
                COUNT(DISTINCT order_id)                AS order_count,
                SUM(actual_amount)                      AS revenue,
                ROUND(AVG(actual_amount), 2)            AS avg_order_value
            FROM dwd.dwd_orders
            WHERE order_valid_flag = '有效'
            GROUP BY order_hour, order_dow
        """)
        print_row_count(conn, "ads.ads_hourly_traffic", "  ADS.时段流量")

        # --------------------------------------------------
        # ADS-7: 品牌市场份额
        # --------------------------------------------------
        logger.info("  构建 ADS-7: 品牌市场份额...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_brand_share AS
            WITH brand_sales AS (
                SELECT
                    p.category_l1,
                    p.category_l2,
                    p.brand,
                    SUM(ps.total_actual_amount) AS brand_revenue,
                    SUM(ps.order_count)         AS brand_orders
                FROM dws.dws_daily_product_sales ps
                JOIN dwd.dwd_products p ON ps.product_id = p.product_id
                GROUP BY p.category_l1, p.category_l2, p.brand
            ),
            category_total AS (
                SELECT
                    category_l1,
                    category_l2,
                    SUM(brand_revenue) AS category_total_revenue
                FROM brand_sales
                GROUP BY category_l1, category_l2
            )
            SELECT
                bs.category_l1,
                bs.category_l2,
                bs.brand,
                bs.brand_revenue,
                bs.brand_orders,
                ROUND(bs.brand_revenue * 1.0 / NULLIF(ct.category_total_revenue, 0), 4) AS market_share,
                ROW_NUMBER() OVER (PARTITION BY bs.category_l1, bs.category_l2
                                   ORDER BY bs.brand_revenue DESC) AS rank_in_category
            FROM brand_sales bs
            JOIN category_total ct
                ON bs.category_l1 = ct.category_l1 AND bs.category_l2 = ct.category_l2
        """)
        print_row_count(conn, "ads.ads_brand_share", "  ADS.品牌份额")

        # --------------------------------------------------
        # ADS-8: 折扣效果分析
        # --------------------------------------------------
        logger.info("  构建 ADS-8: 折扣效果分析...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_discount_effectiveness AS
            WITH discount_orders AS (
                SELECT
                    DATE_TRUNC('month', order_date) AS order_month,
                    CASE
                        WHEN discount_rate = 0 THEN '无折扣'
                        WHEN discount_rate < 0.10 THEN '低折扣(0-10%)'
                        WHEN discount_rate < 0.20 THEN '中折扣(10-20%)'
                        WHEN discount_rate < 0.30 THEN '高折扣(20-30%)'
                        ELSE '超高折扣(>30%)'
                    END                              AS discount_bucket,
                    order_id,
                    user_id,
                    actual_amount,
                    quantity
                FROM dwd.dwd_orders
                WHERE order_valid_flag = '有效'
            )
            SELECT
                order_month,
                discount_bucket,
                COUNT(DISTINCT order_id)                                  AS order_count,
                COUNT(DISTINCT user_id)                                   AS unique_buyers,
                SUM(actual_amount)                                        AS total_revenue,
                ROUND(AVG(actual_amount), 2)                              AS avg_order_value
            FROM discount_orders
            GROUP BY order_month, discount_bucket
        """)
        print_row_count(conn, "ads.ads_discount_effectiveness", "  ADS.折扣效果")

        # --------------------------------------------------
        # ADS-9: 用户 RFM 分层
        # --------------------------------------------------
        logger.info("  构建 ADS-9: 用户 RFM 分层...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_user_rfm AS
            WITH user_rfm_raw AS (
                SELECT
                    user_id,
                    DATEDIFF('day', MAX(order_date), (SELECT MAX(order_date) FROM dwd.dwd_orders)) AS recency,
                    COUNT(DISTINCT order_id)                          AS frequency,
                    SUM(actual_amount)                                AS monetary
                FROM dwd.dwd_orders
                WHERE order_valid_flag = '有效'
                GROUP BY user_id
            ),
            rfm_scores AS (
                SELECT
                    user_id,
                    recency,
                    frequency,
                    monetary,
                    NTILE(5) OVER (ORDER BY recency DESC)   AS r_score,
                    NTILE(5) OVER (ORDER BY frequency ASC)  AS f_score,
                    NTILE(5) OVER (ORDER BY monetary ASC)   AS m_score
                FROM user_rfm_raw
            )
            SELECT
                user_id,
                recency,
                frequency,
                monetary,
                r_score,
                f_score,
                m_score,
                (r_score + f_score + m_score) AS rfm_total,
                CASE
                    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN '重要价值用户'
                    WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN '重要发展用户'
                    WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN '重要保持用户'
                    WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN '重要挽留用户'
                    WHEN r_score >= 4 AND f_score <= 2 THEN '新用户'
                    WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN '流失用户'
                    ELSE '一般用户'
                END AS rfm_segment
            FROM rfm_scores
        """)
        print_row_count(conn, "ads.ads_user_rfm", "  ADS.RFM分层")

        # --------------------------------------------------
        # ADS-10: 月度经营汇总
        # --------------------------------------------------
        logger.info("  构建 ADS-10: 月度经营汇总...")
        conn.execute("""
            CREATE OR REPLACE TABLE ads.ads_monthly_summary AS
            WITH monthly AS (
                SELECT
                    DATE_TRUNC('month', order_date) AS order_month,
                    COUNT(DISTINCT order_id)         AS order_count,
                    COUNT(DISTINCT user_id)          AS unique_buyers,
                    SUM(actual_amount)               AS gmv,
                    ROUND(AVG(actual_amount), 2)     AS aov,
                    SUM(discount)                    AS total_discount,
                    COUNT(DISTINCT product_id)       AS active_products
                FROM dwd.dwd_orders
                WHERE order_valid_flag = '有效'
                GROUP BY DATE_TRUNC('month', order_date)
            )
            SELECT
                order_month,
                order_count,
                unique_buyers,
                gmv,
                aov,
                total_discount,
                active_products,
                ROUND((gmv - LAG(gmv) OVER (ORDER BY order_month))
                      / NULLIF(LAG(gmv) OVER (ORDER BY order_month), 0), 4)  AS gmv_mom,
                ROUND((gmv - LAG(gmv, 12) OVER (ORDER BY order_month))
                      / NULLIF(LAG(gmv, 12) OVER (ORDER BY order_month), 0), 4) AS gmv_yoy,
                ROUND(unique_buyers * 1.0 / NULLIF(
                    (SELECT COUNT(DISTINCT user_id) FROM dwd.dwd_users), 0), 4) AS buyer_penetration
            FROM monthly
        """)
        print_row_count(conn, "ads.ads_monthly_summary", "  ADS.月度汇总")

        # 汇总
        logger.info("")
        logger.info("  ADS 层构建完成！共 10 张业务指标表 ✓")
        logger.info("")
        logger.info("  指标表清单：")
        logger.info("    1. ads_daily_kpi             — 每日经营核心 KPI")
        logger.info("    2. ads_user_cohort           — 用户留存分析")
        logger.info("    3. ads_category_ranking      — 品类月度排名")
        logger.info("    4. ads_city_performance      — 城市业绩表现")
        logger.info("    5. ads_membership_analysis   — 会员等级消费分析")
        logger.info("    6. ads_hourly_traffic        — 时段流量分析")
        logger.info("    7. ads_brand_share           — 品牌市场份额")
        logger.info("    8. ads_discount_effectiveness— 折扣效果分析")
        logger.info("    9. ads_user_rfm              — 用户 RFM 分层")
        logger.info("   10. ads_monthly_summary       — 月度经营汇总")

    except Exception as e:
        logger.error(f"  ADS 构建失败: {e}")
        raise
    finally:
        conn.close()
        logger.debug("  数据库连接已关闭")


if __name__ == "__main__":
    main()
