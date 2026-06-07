# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
# ---

# %% [markdown]
# # 👥 用户行为与商品分析
#
# > **目标**：通过 RFM 模型对用户分层，分析复购与留存，识别高价值品类，探索评分驱动因素。
#
# 核心问题：
# - 用户价值分层如何？高价值用户有什么特征？
# - 复购率和用户留存如何？
# - 哪些商品品类是营收引擎？哪些是长尾？
# - 什么因素导致高/低评分？

# %% [markdown]
# ## 1. 加载数据

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style('whitegrid')

df = pd.read_pickle('./data/01_master_table.pkl')
print(f"✅ 数据加载完成: {df.shape[0]:,} 行")

# %% [markdown]
# ## 2. RFM 用户分层

# %%
# RFM 参考日期：数据集中最后一天 + 1
REFERENCE_DATE = df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)

rfm = df.groupby('customer_unique_id').agg(
    recency=('order_purchase_timestamp', lambda x: (REFERENCE_DATE - x.max()).days),
    frequency=('order_id', 'count'),
    monetary=('total_amount', 'sum')
).reset_index()

# 去除异常：monetary <= 0
rfm = rfm[rfm['monetary'] > 0]

print(f"📊 RFM 统计:")
print(f"   用户数: {len(rfm):,}")
print(f"   Recency   — 中位数: {rfm['recency'].median():.0f} 天")
print(f"   Frequency — 中位数: {rfm['frequency'].median():.0f} 单")
print(f"   Monetary  — 中位数: R$ {rfm['monetary'].median():.0f}")

# %%
# RFM 打分（五分位法）
rfm['R_score'] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)  # recency 越小越好
rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm['M_score'] = pd.qcut(rfm['monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)

rfm['RFM_score'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']

# 用户分层
def segment_rfm(row):
    if row['RFM_score'] >= 13:
        return 'Champions'
    elif row['RFM_score'] >= 10:
        return 'Loyal'
    elif row['RFM_score'] >= 7:
        return 'Potential'
    elif row['RFM_score'] >= 4:
        return 'At Risk'
    else:
        return 'Lost'

rfm['segment'] = rfm.apply(segment_rfm, axis=1)

# 分层汇总
seg_summary = rfm.groupby('segment').agg(
    users=('customer_unique_id', 'count'),
    avg_recency=('recency', 'mean'),
    avg_frequency=('frequency', 'mean'),
    avg_monetary=('monetary', 'mean'),
    total_revenue=('monetary', 'sum')
).reset_index()

seg_order = ['Champions', 'Loyal', 'Potential', 'At Risk', 'Lost']
seg_summary['segment'] = pd.Categorical(seg_summary['segment'], categories=seg_order, ordered=True)
seg_summary = seg_summary.sort_values('segment')
seg_summary['user_pct'] = seg_summary['users'] / seg_summary['users'].sum() * 100
seg_summary['revenue_pct'] = seg_summary['total_revenue'] / seg_summary['total_revenue'].sum() * 100

print("📊 用户分层结果:")
seg_summary

# %%
# 可视化
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 用户数量分布
colors_map = {'Champions': '#1565C0', 'Loyal': '#2196F3', 'Potential': '#64B5F6',
              'At Risk': '#FF7043', 'Lost': '#EF5350'}
seg_colors = [colors_map[s] for s in seg_order if s in seg_summary['segment'].values]
axes[0].pie(seg_summary['users'], labels=seg_summary['segment'], autopct='%1.1f%%',
            colors=seg_colors, startangle=90)
axes[0].set_title('User Distribution by Segment', fontsize=13, fontweight='bold')

# 收入贡献 vs 用户占比
x = np.arange(len(seg_summary))
w = 0.35
axes[1].bar(x - w/2, seg_summary['user_pct'], w, label='User %', color='#42A5F5')
axes[1].bar(x + w/2, seg_summary['revenue_pct'], w, label='Revenue %', color='#EF5350')
axes[1].set_xticks(x)
axes[1].set_xticklabels(seg_summary['segment'], rotation=20)
axes[1].set_title('User % vs Revenue %', fontsize=13, fontweight='bold')
axes[1].legend()
axes[1].set_ylabel('Percentage (%)')

# 各层平均指标对比 (归一化)
metrics = ['avg_recency', 'avg_frequency', 'avg_monetary']
norm_data = seg_summary[metrics].copy()
for col in metrics:
    norm_data[col] = (norm_data[col] - norm_data[col].min()) / (norm_data[col].max() - norm_data[col].min())
norm_data.index = seg_summary['segment']

x = np.arange(len(metrics))
w = 0.15
for i, (seg, row) in enumerate(norm_data.iterrows()):
    axes[2].bar(x + i * w, row.values, w, label=seg, color=colors_map.get(seg, '#999'))
axes[2].set_xticks(x + w * 2)
axes[2].set_xticklabels(['Recency (low=good)', 'Frequency', 'Monetary'])
axes[2].set_title('Normalized RFM by Segment', fontsize=13, fontweight='bold')
axes[2].legend(fontsize=8)

plt.tight_layout()
plt.savefig('./images/03_rfm_segmentation.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 3. 复购与留存分析

# %%
# 复购率：购买 >= 2 次的用户
repeat_users = (rfm['frequency'] >= 2).sum()
print(f"📊 复购用户: {repeat_users:,} / {len(rfm):,} = {repeat_users/len(rfm)*100:.1f}%")

# 购买频次分布
freq_dist = rfm['frequency'].value_counts().sort_index()
freq_dist_pct = freq_dist / freq_dist.sum() * 100

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 频次分布
axes[0].bar(freq_dist.index[:15], freq_dist.values[:15], color='#7E57C2', edgecolor='white')
axes[0].set_title('Purchase Frequency Distribution', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Number of Orders')
axes[0].set_ylabel('Users')

# 复购间隔
repeat_customers = df[df['customer_unique_id'].isin(
    rfm[rfm['frequency'] >= 2]['customer_unique_id']
)].copy()
repeat_customers = repeat_customers.sort_values(['customer_unique_id', 'order_purchase_timestamp'])
repeat_customers['prev_order'] = repeat_customers.groupby('customer_unique_id')['order_purchase_timestamp'].shift(1)
repeat_customers['days_since_last'] = (
    repeat_customers['order_purchase_timestamp'] - repeat_customers['prev_order']
).dt.days
repurchase_intervals = repeat_customers['days_since_last'].dropna()
repurchase_intervals = repurchase_intervals[repurchase_intervals > 0]

axes[1].hist(repurchase_intervals.clip(0, 180), bins=60, color='#26A69A', edgecolor='white')
axes[1].axvline(repurchase_intervals.median(), color='red', linestyle='--',
                label=f'Median: {repurchase_intervals.median():.0f} days')
axes[1].set_title('Repurchase Interval Distribution', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Days Between Purchases')
axes[1].legend()

plt.tight_layout()
plt.savefig('./images/03_repurchase.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"📊 复购间隔中位数: {repurchase_intervals.median():.0f} 天")
print(f"📊 30天内复购占比: {(repurchase_intervals <= 30).sum() / len(repurchase_intervals) * 100:.1f}%")

# %% [markdown]
# ## 4. 用户首次购买 Cohort 分析

# %%
# 计算每个用户首次购买月份
df['purchase_month'] = df['order_purchase_timestamp'].dt.to_period('M')
first_purchase = df.groupby('customer_unique_id')['purchase_month'].min().reset_index()
first_purchase.columns = ['customer_unique_id', 'cohort_month']

df_cohort = df.merge(first_purchase, on='customer_unique_id')
df_cohort['cohort_index'] = (
    (df_cohort['purchase_month'] - df_cohort['cohort_month']).apply(lambda x: x.n)
)

# 构建留存矩阵
cohort_pivot = df_cohort.groupby(['cohort_month', 'cohort_index']).agg(
    n_customers=('customer_unique_id', 'nunique')
).reset_index()

cohort_sizes = cohort_pivot[cohort_pivot['cohort_index'] == 0][['cohort_month', 'n_customers']]
cohort_sizes.columns = ['cohort_month', 'cohort_size']
cohort_pivot = cohort_pivot.merge(cohort_sizes, on='cohort_month')
cohort_pivot['retention'] = cohort_pivot['n_customers'] / cohort_pivot['cohort_size'] * 100

# 透视
retention_matrix = cohort_pivot.pivot_table(
    index='cohort_month', columns='cohort_index', values='retention', aggfunc='mean'
)

# 可视化（取前 12 个 cohort）
fig, ax = plt.subplots(figsize=(14, 8))
display_matrix = retention_matrix.iloc[:12, :12]
sns.heatmap(display_matrix, annot=True, fmt='.1f', cmap='YlOrRd',
            linewidths=0.5, ax=ax, cbar_kws={'label': 'Retention %'})
ax.set_title('Monthly Cohort Retention Matrix (%)', fontsize=15, fontweight='bold')
ax.set_xlabel('Months Since First Purchase')
ax.set_ylabel('First Purchase Month')
plt.tight_layout()
plt.savefig('./images/03_cohort_retention.png', dpi=150, bbox_inches='tight')
plt.show()

# 平均留存曲线
avg_retention = retention_matrix.mean(axis=0)[:12]
print("📊 平均月度留存率:")
for i, r in enumerate(avg_retention):
    print(f"   Month {i}: {r:.1f}%")

# %% [markdown]
# ## 5. 商品品类分析

# %%
# 加载商品数据（含品类）
df_items = pd.read_csv('./data/olist_order_items_dataset.csv')
df_products = pd.read_csv('./data/olist_products_dataset.csv')
df_category = pd.read_csv('./data/product_category_name_translation.csv')
df_products = df_products.merge(df_category, on='product_category_name', how='left')

# 关联到 delivered 订单
order_items_full = df_items.merge(
    df[['order_id']], on='order_id', how='inner'
).merge(
    df_products[['product_id', 'product_category_name_english']], on='product_id', how='left'
)

# 品类汇总
cat_stats = order_items_full.groupby('product_category_name_english').agg(
    items_sold=('order_item_id', 'count'),
    revenue=('price', 'sum'),
    avg_price=('price', 'mean'),
    unique_products=('product_id', 'nunique')
).reset_index()
cat_stats = cat_stats.sort_values('revenue', ascending=False)
cat_stats['revenue_pct'] = cat_stats['revenue'] / cat_stats['revenue'].sum() * 100
cat_stats['cum_revenue_pct'] = cat_stats['revenue_pct'].cumsum()

print("📊 品类营收 TOP 15:")
cat_stats.head(15)[['product_category_name_english', 'revenue', 'revenue_pct', 'items_sold', 'avg_price']]

# %%
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# TOP 15 品类收入
top15 = cat_stats.head(15)
axes[0].barh(range(len(top15)), top15['revenue'] / 1e6, color='#1565C0')
axes[0].set_yticks(range(len(top15)))
axes[0].set_yticklabels(top15['product_category_name_english'], fontsize=9)
axes[0].invert_yaxis()
axes[0].set_title('Top 15 Categories by Revenue', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Revenue (M BRL)')

# 帕累托图 (长尾效应)
axes[1].fill_between(range(len(cat_stats)), cat_stats['cum_revenue_pct'], alpha=0.3, color='#7B1FA2')
axes[1].plot(range(len(cat_stats)), cat_stats['cum_revenue_pct'], color='#4A148C', linewidth=2)
axes[1].axhline(80, color='red', linestyle='--', alpha=0.7)
n_80 = (cat_stats['cum_revenue_pct'] <= 80).sum()
axes[1].axvline(n_80, color='red', linestyle='--', alpha=0.7)
axes[1].annotate(f'{n_80} categories\n= 80% revenue',
                xy=(n_80, 80), xytext=(n_80 + 15, 60),
                arrowprops=dict(arrowstyle='->'), fontsize=10)
axes[1].set_title('Revenue Concentration (Pareto)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Number of Categories')
axes[1].set_ylabel('Cumulative Revenue %')

# 价格与销量散点图
axes[2].scatter(cat_stats['avg_price'], cat_stats['items_sold'] / 1000,
                s=cat_stats['revenue'] / cat_stats['revenue'].max() * 300,
                alpha=0.6, c='#FF7043', edgecolors='white')
axes[2].set_xlabel('Average Price (BRL)')
axes[2].set_ylabel('Items Sold (K)')
axes[2].set_title('Price vs Volume by Category', fontsize=13, fontweight='bold')
# 标注 TOP 5
for i, row in cat_stats.head(5).iterrows():
    axes[2].annotate(row['product_category_name_english'][:20],
                    (row['avg_price'], row['items_sold'] / 1000),
                    fontsize=7, alpha=0.8)

plt.tight_layout()
plt.savefig('./images/03_category_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 6. 评分驱动因素分析

# %%
# 关联评价数据
df_reviews = pd.read_csv('./data/olist_order_reviews_dataset.csv')
reviews_score = df_reviews.groupby('order_id')['review_score'].last().reset_index()
df_with_score = df.merge(reviews_score, on='order_id', how='inner')

# %%
# 评分 vs 物流时效
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 物流时效 vs 评分
delivery_by_score = df_with_score.groupby('review_score')['delivery_time_days'].mean()
axes[0].bar(delivery_by_score.index, delivery_by_score.values,
            color=['#EF5350', '#FF7043', '#FFC107', '#66BB6A', '#43A047'])
axes[0].set_title('Avg Delivery Days by Review Score', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Review Score')
axes[0].set_ylabel('Avg Delivery Days')

# 评分分布百分比
score_pct = df_with_score['review_score'].value_counts(normalize=True).sort_index() * 100
axes[1].bar(score_pct.index, score_pct.values,
            color=['#EF5350', '#FF7043', '#FFC107', '#66BB6A', '#43A047'])
axes[1].set_title('Review Score Distribution (%)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Score')
for i, v in enumerate(score_pct.values):
    axes[1].text(i+1, v + 0.5, f'{v:.1f}%', ha='center', fontweight='bold')

# 订单金额 vs 评分
aov_by_score = df_with_score.groupby('review_score')['total_amount'].mean()
axes[2].bar(aov_by_score.index, aov_by_score.values,
            color=['#EF5350', '#FF7043', '#FFC107', '#66BB6A', '#43A047'])
axes[2].set_title('Avg Order Value by Review Score', fontsize=13, fontweight='bold')
axes[2].set_xlabel('Review Score')
axes[2].set_ylabel('Avg Order Value (BRL)')

plt.tight_layout()
plt.savefig('./images/03_review_analysis.png', dpi=150, bbox_inches='tight')
plt.show()

# %%
# 相关性分析
corr_cols = ['review_score', 'delivery_time_days', 'delivery_delay_days',
             'total_amount', 'total_freight', 'items_count', 'total_installments']
corr_df = df_with_score[corr_cols].dropna()

corr_matrix = corr_df.corr()

fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.3f', cmap='RdBu_r',
            center=0, linewidths=0.5, ax=ax, square=True)
ax.set_title('Correlation Matrix: Review Score & Key Metrics', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('./images/03_correlation.png', dpi=150, bbox_inches='tight')
plt.show()

# 关键发现
print(f"""
📊 评分与关键指标的相关性:
   delivery_delay vs score:        {corr_matrix.loc['review_score','delivery_delay_days']:.4f}
   delivery_time vs score:         {corr_matrix.loc['review_score','delivery_time_days']:.4f}
   freight vs score:               {corr_matrix.loc['review_score','total_freight']:.4f}
   order_amount vs score:          {corr_matrix.loc['review_score','total_amount']:.4f}
""")

# %% [markdown]
# ## 7. 商品品类 × 评分交叉分析

# %%
# 关联商品品类到评分
order_items_full = df_items.merge(
    df_with_score[['order_id', 'review_score']], on='order_id', how='inner'
).merge(
    df_products[['product_id', 'product_category_name_english']], on='product_id', how='left'
)

# 品类评分
cat_score = order_items_full.groupby('product_category_name_english').agg(
    avg_score=('review_score', 'mean'),
    items_sold=('order_item_id', 'count'),
    revenue=('price', 'sum')
).reset_index()
cat_score = cat_score[cat_score['items_sold'] >= 100].sort_values('avg_score', ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# TOP 评分品类
top_score = cat_score.head(10)
axes[0].barh(range(len(top_score)), top_score['avg_score'], color='#43A047')
axes[0].set_yticks(range(len(top_score)))
axes[0].set_yticklabels(top_score['product_category_name_english'], fontsize=9)
axes[0].invert_yaxis()
axes[0].set_title('Top 10 Highest Rated Categories', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Average Review Score')
axes[0].set_xlim(3, 5)

# BOTTOM 评分品类
bottom_score = cat_score.tail(10)
axes[1].barh(range(len(bottom_score)), bottom_score['avg_score'], color='#EF5350')
axes[1].set_yticks(range(len(bottom_score)))
axes[1].set_yticklabels(bottom_score['product_category_name_english'], fontsize=9)
axes[1].invert_yaxis()
axes[1].set_title('Bottom 10 Lowest Rated Categories', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Average Review Score')
axes[1].set_xlim(2, 5)

plt.tight_layout()
plt.savefig('./images/03_category_scores.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 8. 用户与商品 — 综合洞察

# %%
print(f"""
============================================================
📊 用户行为与商品分析 — 核心发现
============================================================

👥 用户分层 (RFM):
   - Champions + Loyal: {(seg_summary[seg_summary['segment'].isin(['Champions','Loyal'])]['users'].sum() / seg_summary['users'].sum() * 100):.1f}% 用户
   - 高价值用户贡献: {(seg_summary[seg_summary['segment'].isin(['Champions','Loyal'])]['revenue_pct'].sum()):.1f}% 收入
   - At Risk + Lost: {(seg_summary[seg_summary['segment'].isin(['At Risk','Lost'])]['users'].sum() / seg_summary['users'].sum() * 100):.1f}% 用户（需激活）

🔄 复购行为:
   - 复购率: {repeat_users/len(rfm)*100:.1f}%
   - 复购间隔中位数: {repurchase_intervals.median():.0f} 天
   - 30天内复购: {(repurchase_intervals <= 30).sum() / len(repurchase_intervals) * 100:.1f}%

📦 商品分析:
   - 营收 TOP 3 品类: {', '.join(cat_stats.head(3)['product_category_name_english'].tolist())}
   - {n_80} 个品类贡献 80% 收入（共 {len(cat_stats)} 个品类）
   - 高价 vs 高量：{cat_stats.head(1)['product_category_name_english'].values[0]} 是营收冠军

⭐ 评分洞察:
   - 物流时效是评分最强相关因子（r = {corr_matrix.loc['review_score','delivery_delay_days']:.3f}）
   - 延迟交付显著拉低评分：低分订单平均延迟得更久
   - 客单价对评分影响很小 → 商品质量 + 物流才是核心

🎯 业务建议:
   1. 重点维护 Champions + Loyal 用户（{repeat_users/len(rfm)*100:.1f}% 复购率有提升空间）
   2. At Risk 用户：推送优惠券 + 限时折扣激活
   3. 物流是评分的核心杠杆 → 优化物流 = 提升口碑
   4. 长尾品类可做捆绑销售（{n_80}/{len(cat_stats)} 品类已覆盖 80% 收入）
============================================================
""")
