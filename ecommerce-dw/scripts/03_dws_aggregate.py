"""
ShopEasy 电商数据仓库 - Step 3: DWS 层轻度汇总

功能：
  - 基于 DWD 层创建面向业务实体的日度汇总表
  - 构建 4 张 DWS 宽表：用户/商品/城市/品类 日度汇总
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    load_config, get_db_connection,
    print_step_header, print_row_count, logger
)


def main():
    print_step_header("DWS 层轻度汇总")

    config = load_config()
    conn = get_db_connection(config)

    try:
        # 创建 DWS schema
        conn.execute("CREATE SCHEMA IF NOT EXISTS dws")
        logger.info("  DWS Schema 已就绪")

        # --------------------------------------------------
        # DWS-1: 每日用户订单汇总
        # --------------------------------------------------
        logger.info("  创建 DWS-1: 每日用户订单汇总...")
        conn.execute("""
            CREATE OR REPLACE TABLE dws.dws_daily_user_orders AS
            SELECT
                order_date,
                user_id,
                COUNT(DISTINCT order_id)     AS order_count,
                SUM(quantity)                AS total_quantity,
                SUM(order_amount)            AS total_order_amount,
                SUM(discount)                AS total_discount,
                SUM(actual_amount)           AS total_actual_amount,
                ROUND(AVG(actual_amount), 2) AS avg_order_value,
                COUNT(DISTINCT product_id)   AS distinct_products
            FROM dwd.dwd_orders
            WHERE order_valid_flag = '有效'
            GROUP BY order_date, user_id
        """)
        print_row_count(conn, "dws.dws_daily_user_orders", "  DWS.每日用户订单")

        # --------------------------------------------------
        # DWS-2: 每日商品销售汇总
        # --------------------------------------------------
        logger.info("  创建 DWS-2: 每日商品销售汇总...")
        conn.execute("""
            CREATE OR REPLACE TABLE dws.dws_daily_product_sales AS
            SELECT
                o.order_date,
                o.product_id,
                p.category_l1,
                p.category_l2,
                p.brand,
                p.price_range,
                COUNT(DISTINCT o.order_id)   AS order_count,
                SUM(o.quantity)              AS total_quantity_sold,
                SUM(o.order_amount)          AS total_order_amount,
                SUM(o.discount)              AS total_discount,
                SUM(o.actual_amount)         AS total_actual_amount,
                COUNT(DISTINCT o.user_id)    AS unique_buyers
            FROM dwd.dwd_orders o
            LEFT JOIN dwd.dwd_products p ON o.product_id = p.product_id
            WHERE o.order_valid_flag = '有效'
            GROUP BY o.order_date, o.product_id, p.category_l1, p.category_l2, p.brand, p.price_range
        """)
        print_row_count(conn, "dws.dws_daily_product_sales", "  DWS.每日商品销售")

        # --------------------------------------------------
        # DWS-3: 每日城市销售汇总
        # --------------------------------------------------
        logger.info("  创建 DWS-3: 每日城市销售汇总...")
        conn.execute("""
            CREATE OR REPLACE TABLE dws.dws_daily_city_sales AS
            SELECT
                order_date,
                shipping_city                      AS city,
                COUNT(DISTINCT order_id)           AS order_count,
                COUNT(DISTINCT user_id)            AS unique_buyers,
                SUM(actual_amount)                 AS total_revenue,
                ROUND(AVG(actual_amount), 2)       AS avg_order_value,
                SUM(quantity)                      AS total_quantity
            FROM dwd.dwd_orders
            WHERE order_valid_flag = '有效'
            GROUP BY order_date, shipping_city
        """)
        print_row_count(conn, "dws.dws_daily_city_sales", "  DWS.每日城市销售")

        # --------------------------------------------------
        # DWS-4: 每日品类销售汇总
        # --------------------------------------------------
        logger.info("  创建 DWS-4: 每日品类销售汇总...")
        conn.execute("""
            CREATE OR REPLACE TABLE dws.dws_daily_category_sales AS
            SELECT
                o.order_date,
                p.category_l1,
                p.category_l2,
                COUNT(DISTINCT o.order_id)   AS order_count,
                SUM(o.quantity)              AS total_quantity,
                SUM(o.actual_amount)         AS total_revenue,
                COUNT(DISTINCT o.user_id)    AS unique_buyers,
                COUNT(DISTINCT o.product_id) AS active_products
            FROM dwd.dwd_orders o
            LEFT JOIN dwd.dwd_products p ON o.product_id = p.product_id
            WHERE o.order_valid_flag = '有效'
            GROUP BY o.order_date, p.category_l1, p.category_l2
        """)
        print_row_count(conn, "dws.dws_daily_category_sales", "  DWS.每日品类销售")

        logger.info("")
        logger.info("  DWS 层汇总完成！✓")

    except Exception as e:
        logger.error(f"  DWS 汇总失败: {e}")
        raise
    finally:
        conn.close()
        logger.debug("  数据库连接已关闭")


if __name__ == "__main__":
    main()
