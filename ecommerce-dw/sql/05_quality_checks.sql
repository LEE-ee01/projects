-- ============================================================
-- ShopEasy 电商数据仓库
-- 05: 数据质量检查
-- 说明：在每个 ETL 步骤后运行这些检查，确保数据质量
--       包含：行数检查、空值检查、重复检查、参照完整性检查、业务逻辑检查
-- ============================================================

-- ----------------------------------------------------------
-- Q1: 各层行数合理性检查
-- ----------------------------------------------------------
-- ODS 层应有数据
SELECT 'ODS层-用户表行数' AS check_name, COUNT(*) AS row_count FROM ods.ods_users
UNION ALL
SELECT 'ODS层-商品表行数', COUNT(*) FROM ods.ods_products
UNION ALL
SELECT 'ODS层-订单表行数', COUNT(*) FROM ods.ods_orders
UNION ALL
SELECT 'DWD层-用户表行数', COUNT(*) FROM dwd.dwd_users
UNION ALL
SELECT 'DWD层-商品表行数', COUNT(*) FROM dwd.dwd_products
UNION ALL
SELECT 'DWD层-订单表行数', COUNT(*) FROM dwd.dwd_orders;

-- ----------------------------------------------------------
-- Q2: 关键字段空值率检查
-- ----------------------------------------------------------
SELECT
    'ODS-用户-会员等级空值率' AS check_name,
    ROUND(SUM(CASE WHEN membership_level IS NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4) AS null_rate
FROM ods.ods_users
UNION ALL
SELECT
    'ODS-订单-实付金额空值率',
    ROUND(SUM(CASE WHEN actual_amount IS NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4)
FROM ods.ods_orders
UNION ALL
SELECT
    'DWD-用户-城市空值率',
    ROUND(SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 4)
FROM dwd.dwd_users;

-- ----------------------------------------------------------
-- Q3: 主键唯一性检查
-- ----------------------------------------------------------
SELECT
    'ODS-订单主键重复率' AS check_name,
    ROUND(1 - COUNT(DISTINCT order_id) * 1.0 / COUNT(*), 4) AS dup_rate
FROM ods.ods_orders
UNION ALL
SELECT
    'ODS-用户主键重复率',
    ROUND(1 - COUNT(DISTINCT user_id) * 1.0 / COUNT(*), 4)
FROM ods.ods_users
UNION ALL
SELECT
    'ODS-商品主键重复率',
    ROUND(1 - COUNT(DISTINCT product_id) * 1.0 / COUNT(*), 4)
FROM ods.ods_products;

-- ----------------------------------------------------------
-- Q4: 参照完整性检查
-- ----------------------------------------------------------
-- 订单中的 user_id 是否都在用户表中存在
SELECT
    '订单→用户参照完整性' AS check_name,
    ROUND(COUNT(DISTINCT CASE WHEN u.user_id IS NOT NULL THEN o.user_id END) * 1.0
          / NULLIF(COUNT(DISTINCT o.user_id), 0), 4) AS match_rate
FROM ods.ods_orders o
LEFT JOIN ods.ods_users u ON o.user_id = u.user_id;

-- 订单中的 product_id 是否都在商品表中存在
SELECT
    '订单→商品参照完整性' AS check_name,
    ROUND(COUNT(DISTINCT CASE WHEN p.product_id IS NOT NULL THEN o.product_id END) * 1.0
          / NULLIF(COUNT(DISTINCT o.product_id), 0), 4) AS match_rate
FROM ods.ods_orders o
LEFT JOIN ods.ods_products p ON o.product_id = p.product_id;

-- ----------------------------------------------------------
-- Q5: 业务逻辑检查
-- ----------------------------------------------------------
-- 实付金额不应为负数
SELECT
    '实付金额负数检查' AS check_name,
    SUM(CASE WHEN actual_amount < 0 THEN 1 ELSE 0 END) AS negative_count,
    COUNT(*) AS total_count
FROM ods.ods_orders;

-- 折扣不应超过原价
SELECT
    '折扣超额检查' AS check_name,
    SUM(CASE WHEN discount > order_amount THEN 1 ELSE 0 END) AS over_discount_count
FROM ods.ods_orders;
