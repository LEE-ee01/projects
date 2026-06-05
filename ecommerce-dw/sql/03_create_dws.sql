-- ============================================================
-- ShopEasy 电商数据仓库
-- 03: DWS 层 (Data Warehouse Service) - 服务数据层
-- 说明：DWS 层对 DWD 明细数据进行轻度汇总，面向业务实体
--       构建用户/商品/日期维度的日度汇总宽表
-- ============================================================

-- ----------------------------------------------------------
-- DWS 每日用户订单汇总
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dws.dws_daily_user_orders AS
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
GROUP BY order_date, user_id;

-- ----------------------------------------------------------
-- DWS 每日商品销售汇总
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dws.dws_daily_product_sales AS
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
GROUP BY o.order_date, o.product_id, p.category_l1, p.category_l2, p.brand, p.price_range;

-- ----------------------------------------------------------
-- DWS 每日城市销售汇总
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dws.dws_daily_city_sales AS
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
GROUP BY order_date, shipping_city;

-- ----------------------------------------------------------
-- DWS 每日品类销售汇总
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dws.dws_daily_category_sales AS
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
GROUP BY o.order_date, p.category_l1, p.category_l2;
