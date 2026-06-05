# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
# ---

# %% [markdown]
# # 🗄️ SQL 分析 — Olist 电商数据
#
# > **目标**：使用纯 SQL（SQLite）完成核心分析，展示 SQL 能力。
#
# 本 Notebook 将 CSV 导入 SQLite，然后用 SQL 实现：
# - 多表 JOIN + 聚合
# - 窗口函数 (ROW_NUMBER, LAG, SUM OVER, RANK)
# - CTE (WITH 子句)
# - CASE WHEN 条件逻辑
# - RFM 用户分层（纯 SQL）
# - Cohort 留存分析（纯 SQL）
#
# ⚡ 这些 SQL 写法在实际工作中直接可用（MySQL / PostgreSQL / Hive 均兼容）。

# %% [markdown]
# ## 1. 导入 CSV 到 SQLite

# %%
import sqlite3
import pandas as pd
import os

# 创建 SQLite 数据库
conn = sqlite3.connect('./data/olist.db')
print("✅ SQLite 数据库已创建: data/olist.db")

# 批量导入 CSV
csv_files = {
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'order_reviews': 'olist_order_reviews_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'customers': 'olist_customers_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'category_translation': 'product_category_name_translation.csv',
}

for table, fname in csv_files.items():
    path = os.path.join('./data', fname)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.to_sql(table, conn, if_exists='replace', index=False)
        print(f"✅ {table:25s} → {len(df):>8,} rows")
    else:
        print(f"⚠️  {table:25s} → 文件未找到（请先下载数据集）")

# 创建索引加速查询
conn.executescript("""
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_payments_order ON order_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_order ON order_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_customers_id ON customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_products_id ON products(product_id);
""")
print("✅ 索引已创建")

# %% [markdown]
# ## 2. 多表 JOIN — 构建订单宽表

# %%
# 核心查询：6 表关联，拿到完整订单画像
query_wide = """
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    -- 物流时效
    CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS INTEGER) AS delivery_days,
    -- 是否延迟
    CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
         THEN 1 ELSE 0 END AS is_delayed,
    -- 订单金额
    oi.total_price,
    oi.total_freight,
    oi.total_price + oi.total_freight AS total_amount,
    oi.items_count,
    -- 支付
    op.payment_type,
    op.payment_installments,
    op.payment_value,
    -- 评分
    r.review_score
FROM orders o
INNER JOIN customers c
    ON o.customer_id = c.customer_id
INNER JOIN (
    -- 子查询: 每笔订单的金额汇总
    SELECT
        order_id,
        SUM(price)          AS total_price,
        SUM(freight_value)  AS total_freight,
        COUNT(order_item_id) AS items_count
    FROM order_items
    GROUP BY order_id
) oi ON o.order_id = oi.order_id
LEFT JOIN (
    -- 子查询: 每笔订单的首选支付方式
    SELECT
        order_id,
        payment_type,
        MAX(payment_installments) AS payment_installments,
        SUM(payment_value) AS payment_value,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_sequential) AS rn
    FROM order_payments
    GROUP BY order_id
) op ON o.order_id = op.order_id
LEFT JOIN (
    -- 子查询: 每笔订单的最新评分
    SELECT
        order_id,
        review_score,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date DESC) AS rn
    FROM order_reviews
) r ON o.order_id = r.order_id AND r.rn = 1
WHERE o.order_status = 'delivered'
LIMIT 10
"""

df_wide_sample = pd.read_sql(query_wide, conn)
print("📊 6表JOIN结果 (前10行):")
df_wide_sample

# %% [markdown]
# ## 3. 聚合查询 — 核心 KPI

# %%
query_kpi = """
SELECT
    -- 总量指标
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    COUNT(DISTINCT c.customer_unique_id)                    AS unique_customers,
    ROUND(SUM(oi.price + oi.freight_value), 2)              AS total_revenue,
    ROUND(AVG(oi.price + oi.freight_value), 2)              AS avg_order_value,
    -- 时间范围
    MIN(o.order_purchase_timestamp)                         AS first_order_date,
    MAX(o.order_purchase_timestamp)                         AS last_order_date,
    -- 评分
    ROUND(AVG(r.review_score), 2)                           AS avg_review_score,
    -- 物流
    ROUND(AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)), 1) AS avg_delivery_days
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN (
    SELECT order_id, SUM(price) AS price, SUM(freight_value) AS freight_value
    FROM order_items
    GROUP BY order_id
) oi ON o.order_id = oi.order_id
LEFT JOIN (
    SELECT order_id, review_score,
           ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date DESC) AS rn
    FROM order_reviews
) r ON o.order_id = r.order_id AND r.rn = 1
WHERE o.order_status = 'delivered'
"""

df_kpi = pd.read_sql(query_kpi, conn)
df_kpi

# %% [markdown]
# ## 4. 窗口函数 — 月度趋势 + 环比/同比

# %%
query_monthly = """
WITH monthly_sales AS (
    -- CTE 1: 月度销售汇总
    SELECT
        strftime('%Y-%m', o.order_purchase_timestamp) AS year_month,
        COUNT(DISTINCT o.order_id)                      AS orders,
        ROUND(SUM(oi.price + oi.freight_value), 2)      AS revenue,
        ROUND(AVG(oi.price + oi.freight_value), 2)      AS aov
    FROM orders o
    INNER JOIN (
        SELECT order_id, SUM(price) AS price, SUM(freight_value) AS freight_value
        FROM order_items GROUP BY order_id
    ) oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY strftime('%Y-%m', o.order_purchase_timestamp)
)
SELECT
    year_month,
    orders,
    revenue,
    aov,
    -- 窗口函数: 环比增长
    ROUND((revenue - LAG(revenue) OVER (ORDER BY year_month))
          / LAG(revenue) OVER (ORDER BY year_month) * 100, 2) AS mom_pct,
    -- 窗口函数: 累计营收
    ROUND(SUM(revenue) OVER (ORDER BY year_month), 2)         AS cumulative_revenue,
    -- 窗口函数: 3个月移动平均
    ROUND(AVG(revenue) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS ma_3m
FROM monthly_sales
ORDER BY year_month
"""

df_monthly = pd.read_sql(query_monthly, conn)
print("📊 月度趋势 (含 环比 / 累计 / 移动平均):")
df_monthly

# %% [markdown]
# ## 5. 窗口函数 — 各州排名 + 集中度

# %%
query_state_rank = """
WITH state_sales AS (
    SELECT
        c.customer_state,
        COUNT(DISTINCT o.order_id)                   AS orders,
        ROUND(SUM(oi.price + oi.freight_value), 2)   AS revenue,
        COUNT(DISTINCT c.customer_unique_id)          AS customers
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.customer_id
    INNER JOIN (
        SELECT order_id, SUM(price) AS price, SUM(freight_value) AS freight_value
        FROM order_items GROUP BY order_id
    ) oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_state
)
SELECT
    customer_state,
    orders,
    revenue,
    customers,
    -- 窗口函数: 排名 (ORDER BY revenue DESC)
    RANK() OVER (ORDER BY revenue DESC)               AS revenue_rank,
    -- 窗口函数: 占比
    ROUND(revenue / SUM(revenue) OVER () * 100, 2)    AS revenue_pct,
    -- 窗口函数: 累计占比 (帕累托)
    ROUND(SUM(revenue) OVER (ORDER BY revenue DESC)
          / SUM(revenue) OVER () * 100, 2)            AS cumulative_pct
FROM state_sales
ORDER BY revenue DESC
LIMIT 10
"""

df_state = pd.read_sql(query_state_rank, conn)
print("📊 各州排名 (RANK + 累计占比):")
df_state

# %% [markdown]
# ## 6. RFM 用户分层 — 纯 SQL 实现

# %%
query_rfm = """
WITH rfm_raw AS (
    -- Step 1: 计算每个用户的 R/F/M 原始值
    SELECT
        c.customer_unique_id,
        -- Recency: 距最后购买的天数（参考日期: 2018-10-01）
        CAST(julianday('2018-10-01') - julianday(MAX(o.order_purchase_timestamp)) AS INTEGER) AS recency,
        -- Frequency: 购买次数
        COUNT(DISTINCT o.order_id) AS frequency,
        -- Monetary: 累计消费金额
        SUM(oi.price + oi.freight_value) AS monetary
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.customer_id
    INNER JOIN (
        SELECT order_id, SUM(price) AS price, SUM(freight_value) AS freight_value
        FROM order_items GROUP BY order_id
    ) oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scored AS (
    -- Step 2: 用 NTILE 分成 5 档打分
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,
        -- NTILE(5): 将数据均分为5组, 1-5分
        -- Recency: 越小越好 → 反向打分 (6 - NTILE值)
        6 - NTILE(5) OVER (ORDER BY recency ASC)  AS R_score,
        NTILE(5) OVER (ORDER BY frequency ASC)     AS F_score,
        NTILE(5) OVER (ORDER BY monetary ASC)      AS M_score
    FROM rfm_raw
),
rfm_segmented AS (
    -- Step 3: 计算 RFM 总分并分层
    SELECT
        *,
        R_score + F_score + M_score AS rfm_total,
        CASE
            WHEN R_score + F_score + M_score >= 13 THEN 'Champions'
            WHEN R_score + F_score + M_score >= 10 THEN 'Loyal'
            WHEN R_score + F_score + M_score >= 7  THEN 'Potential'
            WHEN R_score + F_score + M_score >= 4  THEN 'At Risk'
            ELSE 'Lost'
        END AS segment
    FROM rfm_scored
)
-- Step 4: 各分层汇总
SELECT
    segment,
    COUNT(*)                                            AS user_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS user_pct,
    ROUND(AVG(recency), 0)                              AS avg_recency_days,
    ROUND(AVG(frequency), 1)                            AS avg_frequency,
    ROUND(AVG(monetary), 0)                             AS avg_monetary,
    ROUND(SUM(monetary), 0)                             AS total_revenue,
    ROUND(SUM(monetary) * 100.0 / SUM(SUM(monetary)) OVER (), 2) AS revenue_pct
FROM rfm_segmented
GROUP BY segment
ORDER BY MIN(rfm_total) DESC
"""

df_rfm = pd.read_sql(query_rfm, conn)
print("📊 RFM 用户分层 (纯SQL, 使用 NTILE + CASE WHEN):")
df_rfm

# %% [markdown]
# ## 7. Cohort 留存分析 — 纯 SQL 实现

# %%
query_cohort = """
WITH first_purchase AS (
    -- Step 1: 每个用户的首次购买月份
    SELECT
        c.customer_unique_id,
        strftime('%Y-%m', MIN(o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
user_orders AS (
    -- Step 2: 每个用户每次购买的月份
    SELECT DISTINCT
        c.customer_unique_id,
        strftime('%Y-%m', o.order_purchase_timestamp) AS purchase_month
    FROM orders o
    INNER JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),
cohort_data AS (
    -- Step 3: 关联首次购买月份，计算 cohort_index
    SELECT
        uo.customer_unique_id,
        fp.cohort_month,
        uo.purchase_month,
        -- cohort_index = 月份差 (0, 1, 2, ...)
        (CAST(strftime('%Y', uo.purchase_month) AS INTEGER) -
         CAST(strftime('%Y', fp.cohort_month) AS INTEGER)) * 12
        + (CAST(strftime('%m', uo.purchase_month) AS INTEGER) -
           CAST(strftime('%m', fp.cohort_month) AS INTEGER)) AS cohort_index
    FROM user_orders uo
    INNER JOIN first_purchase fp ON uo.customer_unique_id = fp.customer_unique_id
),
cohort_sizes AS (
    -- Step 4: 每个 cohort 的总用户数 (cohort_index = 0)
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM cohort_data
    WHERE cohort_index = 0
    GROUP BY cohort_month
),
retention AS (
    -- Step 5: 每个 cohort 在每个月仍活跃的用户数
    SELECT
        cd.cohort_month,
        cd.cohort_index,
        COUNT(DISTINCT cd.customer_unique_id) AS active_users
    FROM cohort_data cd
    GROUP BY cd.cohort_month, cd.cohort_index
)
-- Step 6: 计算留存率
SELECT
    r.cohort_month,
    r.cohort_index,
    r.active_users,
    cs.cohort_size,
    ROUND(r.active_users * 100.0 / cs.cohort_size, 2) AS retention_pct
FROM retention r
INNER JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
WHERE r.cohort_index <= 12  -- 只看前12个月
ORDER BY r.cohort_month, r.cohort_index
"""

df_cohort = pd.read_sql(query_cohort, conn)
print("📊 Cohort 留存 (纯SQL, 使用多CTE + 窗口计算):")
df_cohort.head(20)

# %%
# 透视展示
cohort_pivot = df_cohort.pivot_table(
    index='cohort_month', columns='cohort_index', values='retention_pct'
)
print("📊 留存矩阵 (%):")
cohort_pivot.iloc[:8, :8]

# %% [markdown]
# ## 8. CASE WHEN — 订单分层与标签化

# %%
query_case = """
SELECT
    o.order_id,
    oi.total_amount,
    -- CASE WHEN: 订单金额分层
    CASE
        WHEN oi.total_amount < 100                        THEN 'Low (<100)'
        WHEN oi.total_amount BETWEEN 100 AND 300          THEN 'Medium (100-300)'
        WHEN oi.total_amount BETWEEN 300 AND 800          THEN 'High (300-800)'
        ELSE 'VIP (>800)'
    END AS order_tier,
    -- CASE WHEN: 物流表现标签
    CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
        THEN 'On Time / Early'
        WHEN CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) AS INTEGER) <= 5
        THEN 'Slight Delay (≤5d)'
        WHEN CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) AS INTEGER) <= 15
        THEN 'Moderate Delay (6-15d)'
        ELSE 'Severe Delay (>15d)'
    END AS delivery_label,
    -- CASE WHEN: 购买时段
    CASE
        WHEN CAST(strftime('%H', o.order_purchase_timestamp) AS INTEGER) BETWEEN 6 AND 11  THEN 'Morning'
        WHEN CAST(strftime('%H', o.order_purchase_timestamp) AS INTEGER) BETWEEN 12 AND 17 THEN 'Afternoon'
        WHEN CAST(strftime('%H', o.order_purchase_timestamp) AS INTEGER) BETWEEN 18 AND 22 THEN 'Evening'
        ELSE 'Night'
    END AS purchase_period
FROM orders o
INNER JOIN (
    SELECT order_id, SUM(price + freight_value) AS total_amount
    FROM order_items GROUP BY order_id
) oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
LIMIT 15
"""

df_case = pd.read_sql(query_case, conn)
df_case

# %%
# CASE WHEN 聚合分析
query_case_agg = """
WITH labeled AS (
    SELECT
        o.order_id,
        oi.total_amount,
        CASE
            WHEN oi.total_amount < 100 THEN 'Low'
            WHEN oi.total_amount BETWEEN 100 AND 300 THEN 'Medium'
            WHEN oi.total_amount BETWEEN 300 AND 800 THEN 'High'
            ELSE 'VIP'
        END AS order_tier,
        CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time'
            ELSE 'Delayed'
        END AS on_time_flag
    FROM orders o
    INNER JOIN (
        SELECT order_id, SUM(price + freight_value) AS total_amount
        FROM order_items GROUP BY order_id
    ) oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
)
SELECT
    order_tier,
    COUNT(*)                                              AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2)   AS pct,
    ROUND(AVG(total_amount), 0)                           AS avg_amount,
    -- 准时率 (条件聚合)
    ROUND(SUM(CASE WHEN on_time_flag = 'On Time' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate
FROM labeled
GROUP BY order_tier
ORDER BY MIN(CASE order_tier WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 WHEN 'High' THEN 3 ELSE 4 END)
"""

df_case_agg = pd.read_sql(query_case_agg, conn)
print("📊 订单分层 × 准时率 (CASE WHEN + 条件聚合):")
df_case_agg

# %% [markdown]
# ## 9. HAVING + 子查询 — 筛选高价值品类

# %%
query_having = """
SELECT
    p.product_category_name,
    ct.product_category_name_english,
    COUNT(DISTINCT oi.order_id)            AS order_count,
    SUM(oi.price)                          AS total_revenue,
    ROUND(AVG(oi.price), 2)                AS avg_price,
    COUNT(DISTINCT oi.product_id)          AS unique_products
FROM order_items oi
INNER JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
INNER JOIN orders o ON oi.order_id = o.order_id AND o.order_status = 'delivered'
GROUP BY p.product_category_name
-- HAVING: 筛选订单数 >= 100 的品类
HAVING order_count >= 100
   -- 且平均价格在合理范围
   AND avg_price > 0
ORDER BY total_revenue DESC
LIMIT 10
"""

df_having = pd.read_sql(query_having, conn)
df_having

# %% [markdown]
# ## 10. 按月 + 品类交叉分析 (多维度 GROUP BY)

# %%
query_cross = """
WITH monthly_category AS (
    SELECT
        strftime('%Y-%m', o.order_purchase_timestamp) AS year_month,
        ct.product_category_name_english               AS category,
        COUNT(DISTINCT o.order_id)                      AS orders,
        SUM(oi.price)                                   AS revenue
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    INNER JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    WHERE o.order_status = 'delivered'
      AND ct.product_category_name_english IN (
          'bed_bath_table', 'health_beauty', 'watches_gifts',
          'sports_leisure', 'computers_accessories'
      )
    GROUP BY strftime('%Y-%m', o.order_purchase_timestamp), ct.product_category_name_english
)
SELECT
    year_month,
    category,
    orders,
    revenue,
    -- 窗口函数: 品类内月度排名
    RANK() OVER (PARTITION BY year_month ORDER BY revenue DESC) AS monthly_rank,
    -- 窗口函数: 品类营收在各月的占比
    ROUND(revenue * 100.0 / SUM(revenue) OVER (PARTITION BY year_month), 2) AS pct_of_month
FROM monthly_category
ORDER BY year_month, revenue DESC
"""

df_cross = pd.read_sql(query_cross, conn)
print("📊 月度 × 品类交叉分析 (多维度 GROUP BY + 窗口排名):")
df_cross.head(20)

# %% [markdown]
# ## 11. 子查询实战 — 高于平均客单价的订单特征

# %%
query_subquery = """
SELECT
    delivery_label,
    COUNT(*)                                                AS order_count,
    ROUND(AVG(total_amount), 0)                             AS avg_amount,
    ROUND(AVG(review_score), 2)                             AS avg_score,
    ROUND(AVG(delivery_days), 1)                            AS avg_delivery_days
FROM (
    -- 子查询: 筛选高于平均客单价的订单
    SELECT
        o.order_id,
        oi.total_amount,
        r.review_score,
        CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) AS INTEGER) AS delivery_days,
        CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time'
            WHEN CAST(julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) AS INTEGER) <= 5 THEN 'Slight Delay'
            ELSE 'Severe Delay'
        END AS delivery_label
    FROM orders o
    INNER JOIN (
        SELECT order_id, SUM(price + freight_value) AS total_amount
        FROM order_items GROUP BY order_id
    ) oi ON o.order_id = oi.order_id
    LEFT JOIN (
        SELECT order_id, review_score,
               ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_creation_date DESC) AS rn
        FROM order_reviews
    ) r ON o.order_id = r.order_id AND r.rn = 1
    WHERE o.order_status = 'delivered'
      -- 子查询嵌入: 高于平均值
      AND oi.total_amount > (
          SELECT AVG(price + freight_value)
          FROM (
              SELECT order_id, SUM(price + freight_value) AS total
              FROM order_items GROUP BY order_id
          )
      )
) high_value_orders
GROUP BY delivery_label
ORDER BY order_count DESC
"""

df_sub = pd.read_sql(query_subquery, conn)
print("📊 高客单价订单 × 物流表现 (嵌套子查询):")
df_sub

# %% [markdown]
# ## 12. SQL 能力总结

# %%
print("""
================================================================================
🗄️ 本 Notebook 展示的 SQL 技能矩阵
================================================================================

✅ 多表 JOIN             INNER JOIN / LEFT JOIN / 6表关联
✅ 聚合函数              COUNT / SUM / AVG / MAX / MIN + GROUP BY
✅ 子查询                嵌套子查询 (WHERE col > (SELECT AVG(...)))
✅ 窗口函数              ROW_NUMBER / RANK / NTILE / LAG / SUM OVER / AVG OVER
✅ CTE                   WITH ... AS (多个CTE串联)
✅ CASE WHEN             条件分层 / 条件聚合 (SUM(CASE WHEN ...))
✅ HAVING                GROUP BY 后过滤
✅ 日期函数              strftime / julianday / 日期差计算
✅ 索引优化              CREATE INDEX 加速 JOIN
✅ 业务分析              RFM / Cohort / 帕累托 / 月度趋势 / 交叉分析

================================================================================
💡 面试时你可以说:
   "我用 SQLite 搭建了完整的电商数据分析环境，所有核心分析（RFM、
    Cohort、月度趋势、品类交叉）全部用纯 SQL 实现，包括窗口函数、
    CTE 和嵌套子查询。如果需要迁移到 MySQL/PostgreSQL，只需调整
    日期函数即可。"
================================================================================
""")

# %%
conn.close()
print("✅ SQLite 连接已关闭")
