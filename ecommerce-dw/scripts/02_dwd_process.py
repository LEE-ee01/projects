"""
ShopEasy 电商数据仓库 - Step 2: DWD 层数据清洗

功能：
  - 基于 ODS 层数据执行清洗和标准化
  - 创建 DWD schema 和表结构
  - 空值填充、重复处理、日期维度拆分
  - 验证清洗后行数与 ODS 一致
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    load_config, get_db_connection,
    print_step_header, print_row_count, logger,
    check_null_rate, check_duplicates
)


def create_dwd_users(conn) -> None:
    """创建 DWD 用户表：清洗 + 标准化"""
    logger.info("  创建 DWD 用户表...")

    conn.execute("""
        CREATE OR REPLACE TABLE dwd.dwd_users AS
        SELECT
            user_id,
            CAST(register_time AS DATE)          AS register_time,
            EXTRACT(YEAR FROM CAST(register_time AS DATE))   AS register_year,
            EXTRACT(MONTH FROM CAST(register_time AS DATE))  AS register_month,
            TRIM(COALESCE(city, '未知'))           AS city,
            membership_level,
            channel,
            COALESCE(gender, '未知')               AS gender,
            COALESCE(age_group, '未知')            AS age_group
        FROM ods.ods_users
    """)

    print_row_count(conn, "dwd.dwd_users", "  DWD.用户表")

    # 质量检查
    check_null_rate(conn, "dwd.dwd_users", "city")
    check_null_rate(conn, "dwd.dwd_users", "membership_level")


def create_dwd_products(conn) -> None:
    """创建 DWD 商品表：清洗 + 派生毛利率和价格区间"""
    logger.info("  创建 DWD 商品表...")

    conn.execute("""
        CREATE OR REPLACE TABLE dwd.dwd_products AS
        SELECT
            product_id,
            category_l1,
            category_l2,
            COALESCE(brand, '其他品牌')             AS brand,
            unit_price,
            cost_price,
            ROUND((unit_price - cost_price) / NULLIF(unit_price, 0), 4) AS gross_margin,
            CASE
                WHEN unit_price < 50    THEN '0-50元'
                WHEN unit_price < 200   THEN '50-200元'
                WHEN unit_price < 1000  THEN '200-1000元'
                WHEN unit_price < 5000  THEN '1000-5000元'
                ELSE '5000元以上'
            END                                    AS price_range,
            supplier
        FROM ods.ods_products
    """)

    print_row_count(conn, "dwd.dwd_products", "  DWD.商品表")


def create_dwd_orders(conn) -> None:
    """创建 DWD 订单表：清洗 + 日期维度拆分 + 有效性标记"""
    logger.info("  创建 DWD 订单表...")

    conn.execute("""
        CREATE OR REPLACE TABLE dwd.dwd_orders AS
        SELECT
            order_id,
            user_id,
            product_id,
            quantity,
            unit_price,
            order_amount,
            discount,
            discount_rate,
            actual_amount,
            order_status,
            CAST(order_time AS TIMESTAMP)                AS order_time,
            CAST(order_time AS DATE)                     AS order_date,
            EXTRACT(YEAR FROM CAST(order_time AS TIMESTAMP))  AS order_year,
            EXTRACT(MONTH FROM CAST(order_time AS TIMESTAMP)) AS order_month,
            EXTRACT(DAY FROM CAST(order_time AS TIMESTAMP))   AS order_day,
            EXTRACT(DOW FROM CAST(order_time AS TIMESTAMP))   AS order_dow,
            CASE WHEN EXTRACT(DOW FROM CAST(order_time AS TIMESTAMP)) IN (0, 6)
                 THEN '周末' ELSE '工作日' END             AS is_weekend,
            EXTRACT(HOUR FROM CAST(order_time AS TIMESTAMP)) AS order_hour,
            CASE WHEN order_status IN ('已取消', '已退款')
                 THEN '无效' ELSE '有效' END              AS order_valid_flag,
            CASE WHEN payment_time IS NOT NULL
                 THEN CAST(payment_time AS TIMESTAMP) END AS payment_time,
            CASE WHEN payment_time IS NOT NULL
                 THEN CAST(payment_time AS DATE) END      AS payment_date,
            shipping_city
        FROM ods.ods_orders
    """)

    print_row_count(conn, "dwd.dwd_orders", "  DWD.订单表")

    # 质量检查
    check_null_rate(conn, "dwd.dwd_orders", "actual_amount")
    check_null_rate(conn, "dwd.dwd_orders", "order_time")


def verify_row_counts(conn) -> None:
    """验证 DWD 层行数与 ODS 层一致"""
    logger.info("  行数一致性验证...")
    ods_users = conn.execute("SELECT COUNT(*) FROM ods.ods_users").fetchone()[0]
    dwd_users = conn.execute("SELECT COUNT(*) FROM dwd.dwd_users").fetchone()[0]

    ods_orders = conn.execute("SELECT COUNT(*) FROM ods.ods_orders").fetchone()[0]
    dwd_orders = conn.execute("SELECT COUNT(*) FROM dwd.dwd_orders").fetchone()[0]

    ods_products = conn.execute("SELECT COUNT(*) FROM ods.ods_products").fetchone()[0]
    dwd_products = conn.execute("SELECT COUNT(*) FROM dwd.dwd_products").fetchone()[0]

    logger.info(f"  用户表: ODS {ods_users:,} → DWD {dwd_users:,} " + ("✓" if ods_users == dwd_users else "✗ 不一致!"))
    logger.info(f"  商品表: ODS {ods_products:,} → DWD {dwd_products:,} " + ("✓" if ods_products == dwd_products else "✗ 不一致!"))
    logger.info(f"  订单表: ODS {ods_orders:,} → DWD {dwd_orders:,} " + ("✓" if ods_orders == dwd_orders else "✗ 不一致!"))


def main():
    print_step_header("DWD 层数据清洗与标准化")

    config = load_config()
    conn = get_db_connection(config)

    try:
        # 创建 DWD schema
        conn.execute("CREATE SCHEMA IF NOT EXISTS dwd")
        logger.info("  DWD Schema 已就绪")

        # 执行清洗
        create_dwd_users(conn)
        create_dwd_products(conn)
        create_dwd_orders(conn)

        # 验证
        logger.info("")
        verify_row_counts(conn)

        logger.info("")
        logger.info("  DWD 层清洗完成！✓")

    except Exception as e:
        logger.error(f"  DWD 清洗失败: {e}")
        raise
    finally:
        conn.close()
        logger.debug("  数据库连接已关闭")


if __name__ == "__main__":
    main()
