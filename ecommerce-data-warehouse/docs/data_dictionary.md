# ShopEasy 电商数据仓库 — 数据字典

## 源表 (Source)

### 1. users.csv — 用户信息表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | VARCHAR(20) | Y | 用户唯一标识，格式 U000001 |
| register_time | DATE | Y | 注册日期 |
| city | VARCHAR(50) | N | 注册城市 |
| membership_level | VARCHAR(20) | Y | 会员等级（普通/银卡/金卡/钻石/黑金） |
| channel | VARCHAR(20) | N | 注册渠道（APP/小程序/H5网页/PC网页/线下推广） |
| gender | VARCHAR(5) | N | 性别（男/女），约2%缺失 |
| age_group | VARCHAR(20) | N | 年龄段，约1%缺失 |

### 2. products.csv — 商品信息表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | VARCHAR(20) | Y | 商品唯一标识，格式 P00001 |
| category_l1 | VARCHAR(50) | Y | 一级品类（6大类） |
| category_l2 | VARCHAR(50) | Y | 二级品类（30小类） |
| brand | VARCHAR(100) | N | 品牌名称，约2%缺失 |
| unit_price | DECIMAL(12,2) | Y | 售价 |
| cost_price | DECIMAL(12,2) | Y | 成本价 |
| supplier | VARCHAR(50) | N | 供应商 |

### 3. orders.csv — 订单事实表

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_id | VARCHAR(20) | Y | 订单唯一标识，格式 ORD00000001 |
| user_id | VARCHAR(20) | Y | 用户ID（外键→users） |
| product_id | VARCHAR(20) | Y | 商品ID（外键→products） |
| quantity | INT | Y | 购买数量 |
| unit_price | DECIMAL(12,2) | Y | 下单时单价 |
| order_amount | DECIMAL(12,2) | Y | 原价金额（单价×数量） |
| discount | DECIMAL(12,2) | N | 折扣金额 |
| discount_rate | DECIMAL(5,2) | N | 折扣率 |
| actual_amount | DECIMAL(12,2) | Y | 实付金额 |
| order_status | VARCHAR(20) | Y | 订单状态 |
| order_time | TIMESTAMP | Y | 下单时间 |
| payment_time | TIMESTAMP | N | 支付时间 |
| shipping_city | VARCHAR(50) | N | 收货城市 |

---

## ADS 应用层指标表

### ads_daily_kpi — 每日经营核心KPI

| 字段 | 说明 | 计算逻辑 |
|------|------|----------|
| order_date | 订单日期 | — |
| order_count | 有效订单数 | COUNT(DISTINCT order_id) |
| unique_buyers | 下单用户数 | COUNT(DISTINCT user_id) |
| gmv | 总交易额 | SUM(actual_amount) |
| aov | 平均客单价 | GMV / 订单数 |
| orders_per_user | 人均订单数 | 订单数 / 用户数 |
| total_discount | 折扣总额 | SUM(discount) |
| discount_ratio | 折扣率 | 折扣总额 / 原价总额 |
| total_quantity_sold | 总销量 | SUM(quantity) |

### ads_user_rfm — 用户RFM分层

| 字段 | 说明 |
|------|------|
| user_id | 用户ID |
| recency | 距最近一次购买天数 |
| frequency | 累计购买次数 |
| monetary | 累计消费金额 |
| r_score | R分（1-5，越高越好） |
| f_score | F分（1-5，越高越好） |
| m_score | M分（1-5，越高越好） |
| rfm_total | RFM总分（3-15） |
| rfm_segment | 用户分层标签 |

**RFM 分层标签**:
- 重要价值用户 (R≥4, F≥4, M≥4)：核心用户，重点维护
- 重要发展用户 (R≥4, F≥3, M≥3)：有潜力，引导消费
- 重要保持用户 (R≥3, F≥3, M≥3)：稳定用户，保持活跃
- 重要挽留用户 (R≤2, F≥3, M≥3)：曾经高价值，需召回
- 新用户 (R≥4, F≤2)：刚接触，引导复购
- 流失用户 (R≤2, F≤2, M≤2)：基本流失
- 一般用户：其他
