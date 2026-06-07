"""
ShopEasy 电商数据仓库 - 公共工具模块

提供整个 ETL 流程中复用的功能：
  - 配置加载
  - DuckDB 连接管理
  - 日志输出
  - 数据校验辅助函数
"""

import os
import sys
import yaml
import logging
import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ShopEasy-DW")


def load_config(config_path: str = None) -> dict:
    """
    加载 YAML 配置文件。

    Args:
        config_path: 配置文件路径，默认为项目根目录的 config.yaml

    Returns:
        dict: 配置字典
    """
    if config_path is None:
        # 自动定位 config.yaml：脚本所在目录的上一级
        script_dir = Path(__file__).resolve().parent
        config_path = script_dir.parent / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info(f"配置文件加载成功: {config_path}")
    return config


def get_db_connection(config: dict) -> duckdb.DuckDBPyConnection:
    """
    获取 DuckDB 数据库连接。

    每次调用创建新连接（DuckDB 是进程内引擎，连接开销极低）。

    Args:
        config: 配置字典

    Returns:
        duckdb.DuckDBPyConnection: 数据库连接对象
    """
    db_path = config["database"]["path"]

    # 确保数据库目录存在
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(db_path))
    logger.debug(f"DuckDB 连接已建立: {db_path}")
    return conn


def resolve_path(config: dict, key: str) -> Path:
    """
    将配置中的相对路径解析为绝对路径。

    Args:
        config: 配置字典
        key: 配置键（如 "data.raw_dir"）

    Returns:
        Path: 解析后的绝对路径
    """
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    keys = key.split(".")
    value = config
    for k in keys:
        value = value[k]

    path = Path(value)
    if not path.is_absolute():
        path = project_root / path

    return path


def ensure_dir(path: Path) -> None:
    """确保目录存在，不存在则创建。"""
    path.mkdir(parents=True, exist_ok=True)


def print_step_header(step_name: str) -> None:
    """打印步骤标题，方便在日志中定位。"""
    logger.info("=" * 60)
    logger.info(f"  STEP: {step_name}")
    logger.info("=" * 60)


def print_row_count(conn, table_name: str, label: str = None) -> int:
    """
    查询并打印表的行数。

    Args:
        conn: DuckDB 连接
        table_name: 表名
        label: 显示标签

    Returns:
        int: 行数
    """
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    display = label or table_name
    logger.info(f"  {display}: {count:,} 行")
    return count


def check_null_rate(conn, table_name: str, column: str, max_rate: float = 0.05) -> bool:
    """
    检查指定列的空值率。

    Returns:
        bool: 是否通过检查
    """
    total = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    nulls = conn.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE {column} IS NULL"
    ).fetchone()[0]
    rate = nulls / total if total > 0 else 0
    passed = rate <= max_rate
    status = "✓ 通过" if passed else "✗ 未通过"
    logger.info(f"  空值检查 [{column}]: {rate:.2%} (阈值 {max_rate:.0%}) {status}")
    return passed


def check_duplicates(conn, table_name: str, columns: list, max_rate: float = 0.01) -> bool:
    """
    检查指定列组合的重复率。

    Returns:
        bool: 是否通过检查
    """
    cols = ", ".join(columns)
    total = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    unique = conn.execute(
        f"SELECT COUNT(DISTINCT {cols}) FROM {table_name}"
    ).fetchone()[0]
    dup_rate = 1 - (unique / total) if total > 0 else 0
    passed = dup_rate <= max_rate
    status = "✓ 通过" if passed else "✗ 未通过"
    logger.info(f"  重复检查 [{cols}]: {dup_rate:.2%} (阈值 {max_rate:.0%}) {status}")
    return passed


def check_referential_integrity(
    conn, child_table: str, child_col: str,
    parent_table: str, parent_col: str,
    min_rate: float = 0.95
) -> bool:
    """
    检查参照完整性：子表外键在父表中存在的比例。

    Returns:
        bool: 是否通过检查
    """
    result = conn.execute(f"""
        SELECT
            COUNT(DISTINCT c.{child_col}) AS total_fk,
            COUNT(DISTINCT CASE WHEN p.{parent_col} IS NOT NULL THEN c.{child_col} END) AS matched_fk
        FROM {child_table} c
        LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col}
    """).fetchone()

    total_fk, matched_fk = result
    rate = matched_fk / total_fk if total_fk > 0 else 0
    passed = rate >= min_rate
    status = "✓ 通过" if passed else "✗ 未通过"
    logger.info(
        f"  参照完整性 [{child_table}.{child_col} -> {parent_table}.{parent_col}]: "
        f"{rate:.2%} (阈值 {min_rate:.0%}) {status}"
    )
    return passed


def generate_date_range(start_date: str, end_date: str) -> pd.DatetimeIndex:
    """生成日期范围。"""
    return pd.date_range(start=start_date, end=end_date, freq="D")
