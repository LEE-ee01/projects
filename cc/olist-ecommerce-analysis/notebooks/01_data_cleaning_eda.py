# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 📦 Olist 电商数据清洗与探索性分析 (EDA)
#
# > **目标**：理解数据结构、处理缺失值、检测异常值、建立表关联，为后续分析打好基础。
#
# 数据集包含 **9 张表**，覆盖 Olist 平台 2016-2018 年约 10 万笔订单的完整业务链路。

# %% [markdown]
# ## 1. 导入库与设置

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 中文显示设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 显示设置
pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')

print("✅ 库导入完成")

# %% [markdown]
# ## 2. 加载数据

# %%
import os

DATA_DIR = './data'
data = {}

files = {
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'order_reviews': 'olist_order_reviews_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'customers': 'olist_customers_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'geolocation': 'olist_geolocation_dataset.csv',
    'category_translation': 'product_category_name_translation.csv',
}

for name, filename in files.items():
    path = os.path.join(DATA_DIR, filename)
    try:
        data[name] = pd.read_csv(path)
        print(f"✅ {name:25s} → {data[name].shape[0]:>8,} 行 × {data[name].shape[1]:>3} 列")
    except FileNotFoundError:
        print(f"❌ {name:25s} → 文件未找到: {path}")

# %% [markdown]
# ## 3. 数据概览

# %%
# 打印每张表的列名和数据类型
for name, df in data.items():
    print(f"\n{'='*60}")
    print(f"📋 {name} — {df.shape[0]:,} rows × {df.shape[1]} cols")
    print(f"{'='*60}")
    print(df.dtypes.to_string())

# %% [markdown]
# ## 4. 核心表深度清洗

# %% [markdown]
# ### 4.1 订单表 (orders) — 最核心的表

# %%
df_orders = data['orders'].copy()
print(f"👀 前 5 行预览:")
df_orders.head()

# %%
# 检查缺失值
print("📊 缺失值统计:")
missing = df_orders.isnull().sum()
print(missing[missing > 0].sort_values(ascending=False))

# 检查订单状态分布
print(f"\n📊 订单状态分布:")
print(df_orders['order_status'].value_counts())

# %%
# 时间列转换
time_cols = ['order_purchase_timestamp', 'order_approved_at',
             'order_delivered_carrier_date', 'order_delivered_customer_date',
             'order_estimated_delivery_date']

for col in time_cols:
    df_orders[col] = pd.to_datetime(df_orders[col])

# 提取时间维度
df_orders['purchase_year'] = df_orders['order_purchase_timestamp'].dt.year
df_orders['purchase_month'] = df_orders['order_purchase_timestamp'].dt.month
df_orders['purchase_day'] = df_orders['order_purchase_timestamp'].dt.day
df_orders['purchase_dayofweek'] = df_orders['order_purchase_timestamp'].dt.dayofweek
df_orders['purchase_hour'] = df_orders['order_purchase_timestamp'].dt.hour
df_orders['purchase_date'] = df_orders['order_purchase_timestamp'].dt.date

# 计算物流时效（实际送达 vs 预计送达）
df_orders['delivery_time_days'] = (
    df_orders['order_delivered_customer_date'] - df_orders['order_purchase_timestamp']
).dt.days

df_orders['delivery_delay_days'] = (
    df_orders['order_delivered_customer_date'] - df_orders['order_estimated_delivery_date']
).dt.days

# 只保留 delivered 订单用于分析
df_orders_delivered = df_orders[df_orders['order_status'] == 'delivered'].copy()

print(f"📊 时间范围: {df_orders['order_purchase_timestamp'].min()} → {df_orders['order_purchase_timestamp'].max()}")
print(f"📊 delivered 订单: {len(df_orders_delivered):,} / {len(df_orders):,} ({len(df_orders_delivered)/len(df_orders)*100:.1f}%)")

# %% [markdown]
# ### 4.2 订单明细表 (order_items)

# %%
df_items = data['order_items'].copy()
print(f"👀 前 5 行:")
df_items.head()

# %%
print("📊 缺失值检查:")
print(df_items.isnull().sum())

print(f"\n📊 价格统计:")
print(df_items[['price', 'freight_value']].describe())

# 检测异常价格（负值或极端值）
print(f"\n🔍 价格 ≤ 0 的记录: {(df_items['price'] <= 0).sum()}")
print(f"🔍 运费 = 0 的记录: {(df_items['freight_value'] == 0).sum()}")

# 计算每笔订单的总金额和商品数
order_summary = df_items.groupby('order_id').agg(
    items_count=('order_item_id', 'count'),
    total_price=('price', 'sum'),
    total_freight=('freight_value', 'sum')
).reset_index()

order_summary['total_amount'] = order_summary['total_price'] + order_summary['total_freight']

print(f"\n📊 订单汇总统计:")
print(order_summary.describe())

# %% [markdown]
# ### 4.3 支付表 (order_payments)

# %%
df_payments = data['order_payments'].copy()
print("👀 前 5 行:")
df_payments.head()

# %%
print("📊 支付方式分布:")
print(df_payments['payment_type'].value_counts())

print(f"\n📊 分期数统计:")
print(df_payments['payment_installments'].describe())

# %%
# 聚合：每笔订单的总支付金额
payment_agg = df_payments.groupby('order_id').agg(
    total_payment=('payment_value', 'sum'),
    payment_types=('payment_type', lambda x: '|'.join(sorted(set(x)))),
    max_installments=('payment_installments', 'max')
).reset_index()

print(f"👀 支付聚合后:")
payment_agg.head()

# %% [markdown]
# ### 4.4 评价表 (order_reviews)

# %%
df_reviews = data['order_reviews'].copy()
print("📊 评分分布:")
score_dist = df_reviews['review_score'].value_counts().sort_index()
print(score_dist)
print(f"\n平均评分: {df_reviews['review_score'].mean():.2f}")

# %%
# 聚合：每笔订单取最新评价
reviews_agg = df_reviews.sort_values('review_creation_date').groupby('order_id').agg(
    review_score=('review_score', 'last'),
    review_comment=('review_comment_message', 'last')
).reset_index()

print(f"👀 评价聚合后 ({len(reviews_agg):,} 条):")
reviews_agg.head()

# %% [markdown]
# ### 4.5 商品表 (products)

# %%
df_products = data['products'].copy()
# 关联品类英文翻译
df_category = data['category_translation']
df_products = df_products.merge(df_category, on='product_category_name', how='left')

print("📊 品类 TOP 10:")
print(df_products['product_category_name_english'].value_counts().head(10))

print(f"\n📊 商品缺失值:")
print(df_products.isnull().sum())

# %% [markdown]
# ### 4.6 客户表 (customers)

# %%
df_customers = data['customers'].copy()
print("📊 客户地理分布 TOP 10 (州):")
print(df_customers['customer_state'].value_counts().head(10))

print(f"\n📊 客户地理分布 TOP 10 (城市):")
print(df_customers['customer_city'].value_counts().head(10))

print(f"\n📊 唯一客户数: {df_customers['customer_unique_id'].nunique():,}")

# %% [markdown]
# ## 5. 构建分析主表 (宽表)

# %%
# 以 delivered 订单为主键，关联所有维度
df = df_orders_delivered.copy()

# 关联订单金额汇总
df = df.merge(order_summary[['order_id', 'items_count', 'total_price', 'total_freight', 'total_amount']],
              on='order_id', how='left')

# 关联支付
df = df.merge(payment_agg, on='order_id', how='left')

# 关联评价
df = df.merge(reviews_agg[['order_id', 'review_score']], on='order_id', how='left')

# 关联客户
df = df.merge(df_customers[['customer_id', 'customer_unique_id', 'customer_city', 'customer_state']],
              on='customer_id', how='left')

print(f"✅ 分析主表构建完成: {df.shape[0]:,} 行 × {df.shape[1]} 列")
print(f"\n📋 主表列名:")
print(df.columns.tolist())

# %%
# 最终缺失值检查
print("📊 主表缺失值:")
missing_main = df.isnull().sum()
print(missing_main[missing_main > 0])

# %% [markdown]
# ## 6. 探索性数据可视化

# %%
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# 1) 月度订单趋势
monthly_orders = df.groupby(['purchase_year', 'purchase_month']).size().reset_index(name='count')
monthly_orders['period'] = monthly_orders['purchase_year'].astype(str) + '-' + monthly_orders['purchase_month'].astype(str).str.zfill(2)
axes[0, 0].plot(range(len(monthly_orders)), monthly_orders['count'], marker='o', color='#2196F3')
axes[0, 0].set_title('Monthly Order Volume', fontsize=13, fontweight='bold')
axes[0, 0].set_xticks(range(0, len(monthly_orders), 3))
axes[0, 0].set_xticklabels(monthly_orders['period'].iloc[::3], rotation=45, ha='right', fontsize=8)

# 2) 订单状态饼图
status_counts = df_orders['order_status'].value_counts()
axes[0, 1].pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
               colors=sns.color_palette('pastel'), startangle=90)
axes[0, 1].set_title('Order Status Distribution', fontsize=13, fontweight='bold')

# 3) 评分分布
axes[0, 2].bar(score_dist.index, score_dist.values, color=['#EF5350', '#FF7043', '#FFC107', '#66BB6A', '#43A047'])
axes[0, 2].set_title('Review Score Distribution', fontsize=13, fontweight='bold')
axes[0, 2].set_xlabel('Score')
axes[0, 2].set_ylabel('Count')

# 4) 物流时效分布
axes[1, 0].hist(df['delivery_time_days'].clip(0, 60), bins=60, color='#7E57C2', edgecolor='white')
axes[1, 0].axvline(df['delivery_time_days'].median(), color='red', linestyle='--', label=f'Median: {df["delivery_time_days"].median():.0f} days')
axes[1, 0].legend()
axes[1, 0].set_title('Delivery Time Distribution (days)', fontsize=13, fontweight='bold')

# 5) 每小时订单量
hourly = df['purchase_hour'].value_counts().sort_index()
axes[1, 1].bar(hourly.index, hourly.values, color='#26A69A')
axes[1, 1].set_title('Orders by Hour of Day', fontsize=13, fontweight='bold')
axes[1, 1].set_xlabel('Hour')
axes[1, 1].set_xticks(range(0, 24, 3))

# 6) 订单金额分布
axes[1, 2].hist(df['total_amount'].clip(0, df['total_amount'].quantile(0.99)), bins=50,
                color='#FF7043', edgecolor='white')
axes[1, 2].axvline(df['total_amount'].median(), color='blue', linestyle='--', label=f'Median: R${df["total_amount"].median():.0f}')
axes[1, 2].legend()
axes[1, 2].set_title('Order Amount Distribution (BRL)', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('./images/01_eda_overview.png', dpi=150, bbox_inches='tight')
plt.show()
print("✅ EDA 概览图已保存至 images/01_eda_overview.png")

# %% [markdown]
# ## 7. 关键发现 (初步)

# %%
print("""
============================================================
📋 数据清洗阶段 — 关键发现
============================================================

1. 数据规模:
   - {total_orders:,} 笔订单，{delivered:,} 笔已交付 ({delivered_pct:.1f}%)
   - 时间跨度: {date_min} → {date_max}

2. 数据质量:
   - 订单表: {order_missing} 列有缺失值（主要是物流中间节点的时间戳）
   - 商品表: 部分商品缺少尺寸/重量信息
   - 评价表: 留言缺失较多（正常，用户可选不留言）

3. 初步洞察:
   - 评分呈明显右偏: 4-5分占绝大多数
   - 物流时效中位数: {median_delivery:.0f} 天
   - 订单金额中位数: R$ {median_amount:.0f}
   - 信用卡是最主要支付方式
   - 订单量呈上升趋势，有季节性波动
============================================================
""".format(
    total_orders=len(df_orders),
    delivered=len(df_orders_delivered),
    delivered_pct=len(df_orders_delivered)/len(df_orders)*100,
    date_min=df_orders['order_purchase_timestamp'].min().strftime('%Y-%m-%d'),
    date_max=df_orders['order_purchase_timestamp'].max().strftime('%Y-%m-%d'),
    order_missing=df_orders.isnull().sum().gt(0).sum(),
    median_delivery=df['delivery_time_days'].median(),
    median_amount=df['total_amount'].median(),
))

# %% [markdown]
# ## 8. 数据导出 (供后续分析使用)

# %%
# 保存清洗后的主表
df.to_pickle('./data/01_master_table.pkl')
print("✅ 主表已保存至 data/01_master_table.pkl")
print(f"   维度: {df.shape[0]:,} 行 × {df.shape[1]} 列")
print(f"   内存: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
