"""
ShopEasy 电商数据仓库 - Step 1: ODS 层数据加载

功能：
  - 从 raw/ 目录读取原始 CSV 文件
  - 创建 ODS schema 和表结构
  - 将 CSV 数据加载到 DuckDB ODS 表中
  - 执行基本行数验证
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    load_config, get_db_connection, resolve_path,
    print_step_header, print_row_count, logger
)


def load_csv_to_ods(conn, csv_dir: Path, table_name: str) -> None:
    """
    将 CSV 文件读入 DuckDB 并创建 ODS 表。

    使用 DuckDB 的 read_csv_auto 函数自动推断列类型，
    然后 CREATE TABLE AS SELECT 持久化到数据库。

    Args:
        conn: DuckDB 连接
        csv_dir: CSV 文件目录
        table_name: 目标表名（如 "ods_users"）
    """
    # 从表名推导 CSV 文件名
    csv_name = table_name.replace("ods_", "") + ".csv"
    csv_path = csv_dir / csv_name

    if not csv_path.exists():
        logger.error(f"  CSV 文件不存在: {csv_path}")
        return

    logger.info(f"  读取 CSV: {csv_path}")

    # 使用 DuckDB 的 read_csv_auto 自动处理
    conn.execute(f"""
        CREATE OR REPLACE TABLE ods.{table_name} AS
        SELECT * FROM read_csv_auto('{csv_path}', header=true)
    """)

    print_row_count(conn, f"ods.{table_name}", f"  ODS.{table_name}")


def main():
    print_step_header("ODS 层数据加载")

    config = load_config()
    conn = get_db_connection(config)
    csv_dir = resolve_path(config, "data.raw_dir")

    try:
        # 创建 ODS schema
        conn.execute("CREATE SCHEMA IF NOT EXISTS ods")
        logger.info("  ODS Schema 已就绪")

        # 加载三张源表
        load_csv_to_ods(conn, csv_dir, "ods_users")
        load_csv_to_ods(conn, csv_dir, "ods_products")
        load_csv_to_ods(conn, csv_dir, "ods_orders")

        logger.info("")
        logger.info("  ODS 层加载完成！✓")

    except Exception as e:
        logger.error(f"  ODS 加载失败: {e}")
        raise
    finally:
        conn.close()
        logger.debug("  数据库连接已关闭")


if __name__ == "__main__":
    main()
