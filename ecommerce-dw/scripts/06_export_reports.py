"""
ShopEasy 电商数据仓库 - Step 6: 报表导出

功能：
  - 将 ADS 层的 10 张指标表导出为 CSV 文件
  - 生成数据概览摘要
  - 输出文件供 Streamlit 看板和外部工具使用
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    load_config, get_db_connection, resolve_path,
    print_step_header, ensure_dir, logger
)

# ADS 表清单
ADS_TABLES = [
    ("ads_daily_kpi", "每日经营核心KPI"),
    ("ads_user_cohort", "用户留存分析"),
    ("ads_category_ranking", "品类月度排名"),
    ("ads_city_performance", "城市业绩表现"),
    ("ads_membership_analysis", "会员等级消费分析"),
    ("ads_hourly_traffic", "时段流量分析"),
    ("ads_brand_share", "品牌市场份额"),
    ("ads_discount_effectiveness", "折扣效果分析"),
    ("ads_user_rfm", "用户RFM分层"),
    ("ads_monthly_summary", "月度经营汇总"),
]


def export_table(conn, table_name: str, output_dir: Path) -> tuple[int, float]:
    """
    导出单张 ADS 表为 CSV。

    Returns:
        tuple[int, float]: (行数, 文件大小KB)
    """
    # 导出为 CSV
    csv_path = output_dir / f"{table_name}.csv"

    conn.execute(f"""
        COPY (SELECT * FROM ads.{table_name}) TO '{csv_path}'
        (HEADER, DELIMITER ',')
    """)

    # 获取行数
    row_count = conn.execute(f"SELECT COUNT(*) FROM ads.{table_name}").fetchone()[0]
    file_size_kb = csv_path.stat().st_size / 1024

    return row_count, file_size_kb


def print_summary(conn) -> None:
    """打印核心数据摘要。"""
    logger.info("")
    logger.info("=" * 50)
    logger.info("  核心数据摘要")
    logger.info("=" * 50)

    # 总 GMV
    gmv = conn.execute("SELECT SUM(gmv) FROM ads.ads_monthly_summary").fetchone()[0]
    logger.info(f"  累计 GMV:        ¥{gmv:,.2f}")

    # 总订单
    orders = conn.execute("SELECT SUM(order_count) FROM ads.ads_monthly_summary").fetchone()[0]
    logger.info(f"  累计订单数:       {orders:,}")

    # 总用户
    users = conn.execute("SELECT COUNT(*) FROM dwd.dwd_users").fetchone()[0]
    logger.info(f"  累计用户数:       {users:,}")

    # 月均 GMV
    monthly_avg = conn.execute("SELECT AVG(gmv) FROM ads.ads_monthly_summary").fetchone()[0]
    logger.info(f"  月均 GMV:        ¥{monthly_avg:,.2f}")

    # 平均客单价
    aov = conn.execute("SELECT AVG(aov) FROM ads.ads_daily_kpi").fetchone()[0]
    logger.info(f"  平均客单价:       ¥{aov:,.2f}")

    # RFM 分层
    logger.info("")
    logger.info("  用户 RFM 分层分布:")
    rfm_rows = conn.execute("""
        SELECT rfm_segment, COUNT(*) AS cnt,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
        FROM ads.ads_user_rfm
        GROUP BY rfm_segment
        ORDER BY cnt DESC
    """).fetchall()
    for row in rfm_rows:
        logger.info(f"    {row[0]:12s}: {row[1]:,} 人 ({row[2]}%)")


def main():
    print_step_header("ADS 报表导出")

    config = load_config()
    conn = get_db_connection(config)
    reports_dir = resolve_path(config, "output.reports_dir")
    ensure_dir(reports_dir)

    try:
        total_rows = 0
        total_size = 0.0

        logger.info(f"  输出目录: {reports_dir}")
        logger.info("")

        for table_name, description in ADS_TABLES:
            logger.info(f"  导出: {table_name} ({description})...")
            rows, size_kb = export_table(conn, table_name, reports_dir)
            total_rows += rows
            total_size += size_kb
            logger.info(f"    → {rows:,} 行, {size_kb:.1f} KB")

        logger.info("")
        logger.info(f"  导出完成！共 {len(ADS_TABLES)} 张表, {total_rows:,} 行, {total_size:.1f} KB")

        # 打印摘要
        print_summary(conn)

    except Exception as e:
        logger.error(f"  报表导出失败: {e}")
        raise
    finally:
        conn.close()
        logger.debug("  数据库连接已关闭")


if __name__ == "__main__":
    main()
