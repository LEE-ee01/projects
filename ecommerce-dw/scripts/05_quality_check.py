"""
ShopEasy 电商数据仓库 - Step 5: 数据质量检查

功能：
  - 对各层数据进行系统化质量检查
  - 检查项：行数合理性、空值率、主键唯一性、参照完整性、业务逻辑
  - 生成质量报告文本文件
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    load_config, get_db_connection, resolve_path,
    print_step_header, logger, ensure_dir
)


def run_quality_checks(conn) -> list[dict]:
    """
    运行所有数据质量检查。

    Returns:
        list[dict]: 检查结果列表，每项包含 name, status, detail
    """
    results = []

    # ---- Q1: 各层行数合理性 ----
    logger.info("  Q1: 各层行数合理性检查...")
    for schema, table in [("ods", "ods_users"), ("ods", "ods_products"), ("ods", "ods_orders"),
                           ("dwd", "dwd_users"), ("dwd", "dwd_products"), ("dwd", "dwd_orders")]:
        count = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
        passed = count > 0
        results.append({
            "name": f"{schema}.{table} 行数",
            "status": "✓ 通过" if passed else "✗ 失败",
            "detail": f"行数: {count:,}"
        })
        logger.info(f"    {schema}.{table}: {count:,} 行 {'✓' if passed else '✗'}")

    # ---- Q2: ODS vs DWD 行数一致性 ----
    logger.info("  Q2: ODS/DWD 行数一致性检查...")
    for name in ["users", "products", "orders"]:
        ods_count = conn.execute(f"SELECT COUNT(*) FROM ods.ods_{name}").fetchone()[0]
        dwd_count = conn.execute(f"SELECT COUNT(*) FROM dwd.dwd_{name}").fetchone()[0]
        passed = ods_count == dwd_count
        results.append({
            "name": f"{name} 表 ODS/DWD 一致性",
            "status": "✓ 通过" if passed else "✗ 失败",
            "detail": f"ODS: {ods_count:,}, DWD: {dwd_count:,}"
        })
        logger.info(f"    {name}: ODS {ods_count:,} vs DWD {dwd_count:,} {'✓' if passed else '✗'}")

    # ---- Q3: 主键唯一性 ----
    logger.info("  Q3: 主键唯一性检查...")
    for schema, table, pk in [
        ("ods", "ods_users", "user_id"),
        ("ods", "ods_products", "product_id"),
        ("ods", "ods_orders", "order_id"),
    ]:
        total = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
        unique = conn.execute(f"SELECT COUNT(DISTINCT {pk}) FROM {schema}.{table}").fetchone()[0]
        dup_rate = 1 - (unique / total) if total > 0 else 0
        passed = dup_rate == 0
        results.append({
            "name": f"{schema}.{table} 主键唯一性",
            "status": "✓ 通过" if passed else "✗ 失败",
            "detail": f"重复率: {dup_rate:.4f}"
        })
        logger.info(f"    {table}.{pk}: 重复率 {dup_rate:.4f} {'✓' if passed else '✗'}")

    # ---- Q4: 关键字段空值率 ----
    logger.info("  Q4: 关键字段空值率检查...")
    checks = [
        ("dwd.dwd_users", "membership_level", 0.0),
        ("dwd.dwd_users", "city", 0.05),
        ("dwd.dwd_orders", "actual_amount", 0.0),
        ("dwd.dwd_orders", "order_time", 0.0),
        ("dwd.dwd_products", "unit_price", 0.0),
    ]
    for table, col, threshold in checks:
        total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        nulls = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL").fetchone()[0]
        rate = nulls / total if total > 0 else 0
        passed = rate <= threshold
        results.append({
            "name": f"{table}.{col} 空值率",
            "status": "✓ 通过" if passed else "✗ 失败",
            "detail": f"空值率: {rate:.4f} (阈值: {threshold:.0%})"
        })
        logger.info(f"    {table}.{col}: {rate:.4f} {'✓' if passed else '✗'}")

    # ---- Q5: 参照完整性 ----
    logger.info("  Q5: 参照完整性检查...")
    ri_checks = [
        ("ods.ods_orders", "user_id", "ods.ods_users", "user_id"),
        ("ods.ods_orders", "product_id", "ods.ods_products", "product_id"),
    ]
    for child_t, child_c, parent_t, parent_c in ri_checks:
        result = conn.execute(f"""
            SELECT
                COUNT(DISTINCT c.{child_c}) AS total_fk,
                COUNT(DISTINCT CASE WHEN p.{parent_c} IS NOT NULL THEN c.{child_c} END) AS matched_fk
            FROM {child_t} c
            LEFT JOIN {parent_t} p ON c.{child_c} = p.{parent_c}
        """).fetchone()
        total_fk, matched_fk = result
        rate = matched_fk / total_fk if total_fk > 0 else 0
        passed = rate >= 0.95
        results.append({
            "name": f"参照完整性: {child_t}.{child_c} -> {parent_t}.{parent_c}",
            "status": "✓ 通过" if passed else "✗ 失败",
            "detail": f"匹配率: {rate:.4f} (阈值: 95%)"
        })
        logger.info(f"    {child_c}: {rate:.4f} {'✓' if passed else '✗'}")

    # ---- Q6: 业务逻辑检查 ----
    logger.info("  Q6: 业务逻辑检查...")
    logic_checks = [
        ("实付金额非负", "SELECT COUNT(*) FROM ods.ods_orders WHERE actual_amount < 0", True),
        ("折扣不超原价", "SELECT COUNT(*) FROM ods.ods_orders WHERE discount > order_amount", True),
        ("有效订单数>0", "SELECT COUNT(*) FROM dwd.dwd_orders WHERE order_valid_flag = '有效'", False),
    ]
    for name, query, expect_zero in logic_checks:
        count = conn.execute(query).fetchone()[0]
        if expect_zero:
            passed = count == 0
        else:
            passed = count > 0
        results.append({
            "name": f"业务逻辑: {name}",
            "status": "✓ 通过" if passed else "✗ 失败",
            "detail": f"异常数: {count}" if expect_zero else f"数量: {count:,}"
        })
        logger.info(f"    {name}: {'✓' if passed else '✗'}")

    return results


def write_quality_report(results: list[dict], report_path: Path) -> None:
    """将质量检查结果写入文本报告。"""
    ensure_dir(report_path.parent)

    passed_count = sum(1 for r in results if "通过" in r["status"])
    total_count = len(results)

    lines = [
        "=" * 60,
        "  ShopEasy 电商数据仓库 - 数据质量检查报告",
        "=" * 60,
        f"  检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  检查项: {total_count}",
        f"  通过: {passed_count}",
        f"  失败: {total_count - passed_count}",
        f"  通过率: {passed_count/total_count*100:.1f}%",
        "=" * 60,
        "",
    ]

    for i, r in enumerate(results, 1):
        lines.append(f"  [{i:2d}] {r['name']}")
        lines.append(f"       状态: {r['status']}")
        lines.append(f"       详情: {r['detail']}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("  检查完成" + (" ✓ 全部通过!" if passed_count == total_count else ""))

    report_text = "\n".join(lines)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info(f"  质量报告已保存: {report_path}")


def main():
    print_step_header("数据质量检查")

    config = load_config()
    conn = get_db_connection(config)
    report_path = Path(__file__).resolve().parent.parent / config["output"]["quality_report"]

    try:
        results = run_quality_checks(conn)
        write_quality_report(results, report_path)

        # 打印最终结论
        passed = sum(1 for r in results if "通过" in r["status"])
        total = len(results)
        logger.info("")
        logger.info(f"  质量检查完成: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

        if passed < total:
            logger.warning(f"  有 {total - passed} 项检查未通过，请检查报告详情。")
        else:
            logger.info("  ✓ 全部质量检查通过！")

    except Exception as e:
        logger.error(f"  质量检查失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
