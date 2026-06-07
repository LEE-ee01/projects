-- ============================================================
-- ShopEasy 电商数据仓库
-- 02: DWD 层 (Data Warehouse Detail) - 明细数据层
-- 说明：DWD 层对 ODS 数据进行清洗、去重、标准化处理
--       - 去除重复数据
--       - 统一空值处理
--       - 标准化枚举值
--       - 派生日期维度字段
-- ============================================================

-- ----------------------------------------------------------
-- DWD 用户信息表
-- 清洗规则：
--   - gender 空值填充为 "未知"
--   - age_group 空值填充为 "未知"
--   - 标准化城市名称（去除首尾空格）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwd.dwd_users AS
SELECT
    user_id,
    register_time,
    -- 提取注册日期维度
    EXTRACT(YEAR FROM register_time)   AS register_year,
    EXTRACT(MONTH FROM register_time)  AS register_month,
    TRIM(COALESCE(city, '未知'))        AS city,
    membership_level,
    channel,
    COALESCE(gender, '未知')            AS gender,
    COALESCE(age_group, '未知')         AS age_group
FROM ods.ods_users;

-- ----------------------------------------------------------
-- DWD 商品信息表
-- 清洗规则：
--   - brand 空值填充为 "其他品牌"
--   - 计算毛利率: (unit_price - cost_price) / unit_price
--   - 商品价格区间分段
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwd.dwd_products AS
SELECT
    product_id,
    category_l1,
    category_l2,
    COALESCE(brand, '其他品牌')                          AS brand,
    unit_price,
    cost_price,
    ROUND((unit_price - cost_price) / NULLIF(unit_price, 0), 4) AS gross_margin,
    CASE
        WHEN unit_price < 50    THEN '0-50元'
        WHEN unit_price < 200   THEN '50-200元'
        WHEN unit_price < 1000  THEN '200-1000元'
        WHEN unit_price < 5000  THEN '1000-5000元'
        ELSE '5000元以上'
    END                                               AS price_range,
    supplier
FROM ods.ods_products;

-- ----------------------------------------------------------
-- DWD 订单事实表
-- 清洗规则：
--   - 过滤取消订单（仅保留有效订单用于分析）
--   - 派生日期维度：年/月/日/周几/是否周末/小时
--   - 派生订单状态标签（有效/无效）
--   - 计算实付单价
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dwd.dwd_orders AS
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
    order_time,
    -- 日期维度拆分
    CAST(order_time AS DATE)             AS order_date,
    EXTRACT(YEAR FROM order_time)        AS order_year,
    EXTRACT(MONTH FROM order_time)       AS order_month,
    EXTRACT(DAY FROM order_time)         AS order_day,
    EXTRACT(DOW FROM order_time)         AS order_dow,         -- 0=周日
    CASE WHEN EXTRACT(DOW FROM order_time) IN (0, 6)
         THEN '周末' ELSE '工作日' END     AS is_weekend,
    EXTRACT(HOUR FROM order_time)        AS order_hour,
    -- 订单有效性标记
    CASE WHEN order_status IN ('已取消', '已退款')
         THEN '无效' ELSE '有效' END      AS order_valid_flag,
    payment_time,
    CAST(payment_time AS DATE)           AS payment_date,
    shipping_city
FROM ods.ods_orders;
