# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
# ---

# %% [markdown]
# # 📈 销售趋势与业务分析
#
# > **目标**：从时间、地域、支付等多维度分析销售表现，发现增长驱动因素和业务机会。
#
# 核心问题：
# - 销售额和订单量的增长趋势如何？是否存在季节性？
# - 哪些州/城市贡献了最多的收入？
# - 支付方式对客单价有何影响？
# - 一周中哪天、一天中哪个时段是销售高峰？

# %% [markdown]
# ## 1. 加载数据

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style('whitegrid')

df = pd.read_pickle('./data/01_master_table.pkl')
print(f"✅ 数据加载完成: {df.shape[0]:,} 行 × {df.shape[1]} 列")

# %% [markdown]
# ## 2. 营收与订单趋势

# %%
# 月度汇总
df['year_month'] = df['order_purchase_timestamp'].dt.to_period('M')
monthly = df.groupby('year_month').agg(
    orders=('order_id', 'count'),
    revenue=('total_amount', 'sum'),
    avg_order_value=('total_amount', 'mean'),
    customers=('customer_unique_id', 'nunique')
).reset_index()
monthly['year_month'] = monthly['year_month'].astype(str)

monthly.head()

# %%
fig, axes = plt.subplots(2, 2, figsize=(18, 10))

# 1) 月度营收
axes[0, 0].fill_between(range(len(monthly)), monthly['revenue'] / 1e6, alpha=0.3, color='#2196F3')
axes[0, 0].plot(range(len(monthly)), monthly['revenue'] / 1e6, marker='o', color='#1976D2', linewidth=2)
axes[0, 0].set_title('Monthly Revenue (Million BRL)', fontsize=14, fontweight='bold')
axes[0, 0].set_ylabel('Revenue (M BRL)')
axes[0, 0].set_xticks(range(0, len(monthly), 2))
axes[0, 0].set_xticklabels(monthly['year_month'].iloc[::2], rotation=45, ha='right', fontsize=8)

# 添加趋势线
x = np.arange(len(monthly))
z = np.polyfit(x, monthly['revenue'] / 1e6, 1)
p = np.poly1d(z)
axes[0, 0].plot(x, p(x), '--', color='red', linewidth=1.5, label=f'Trend (slope={z[0]:.3f})')
axes[0, 0].legend()

# 2) 月度订单量
axes[0, 1].fill_between(range(len(monthly)), monthly['orders'] / 1000, alpha=0.3, color='#4CAF50')
axes[0, 1].plot(range(len(monthly)), monthly['orders'] / 1000, marker='s', color='#388E3C', linewidth=2)
axes[0, 1].set_title('Monthly Orders (Thousands)', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('Orders (K)')
axes[0, 1].set_xticks(range(0, len(monthly), 2))
axes[0, 1].set_xticklabels(monthly['year_month'].iloc[::2], rotation=45, ha='right', fontsize=8)

# 3) 客单价趋势
axes[1, 0].plot(range(len(monthly)), monthly['avg_order_value'], marker='D', color='#FF7043', linewidth=2)
axes[1, 0].axhline(monthly['avg_order_value'].mean(), color='gray', linestyle='--',
                   label=f'AVG: R$ {monthly["avg_order_value"].mean():.0f}')
axes[1, 0].set_title('Average Order Value Trend (BRL)', fontsize=14, fontweight='bold')
axes[1, 0].set_xticks(range(0, len(monthly), 2))
axes[1, 0].set_xticklabels(monthly['year_month'].iloc[::2], rotation=45, ha='right', fontsize=8)
axes[1, 0].legend()

# 4) 同比增长率
monthly['revenue_pct_change'] = monthly['revenue'].pct_change(12) * 100  # 12个月同比
valid_pct = monthly.dropna(subset=['revenue_pct_change'])
axes[1, 1].bar(range(len(monthly)), monthly['revenue_pct_change'],
               color=['#4CAF50' if v > 0 else '#EF5350' for v in monthly['revenue_pct_change'].fillna(0)])
axes[1, 1].axhline(0, color='black', linewidth=1)
axes[1, 1].set_title('Revenue YoY Growth Rate (%)', fontsize=14, fontweight='bold')
axes[1, 1].set_xticks(range(0, len(monthly), 2))
axes[1, 1].set_xticklabels(monthly['year_month'].iloc[::2], rotation=45, ha='right', fontsize=8)

plt.tight_layout()
plt.savefig('./images/02_revenue_trends.png', dpi=150, bbox_inches='tight')
plt.show()

# 打印关键数字
print(f"📊 总营收: R$ {monthly['revenue'].sum():,.0f}")
print(f"📊 月均营收: R$ {monthly['revenue'].mean():,.0f}")
print(f"📊 月均订单: {monthly['orders'].mean():,.0f}")
print(f"📊 增长斜率 (月): R$ {z[0]*1e6:,.0f}")

# %% [markdown]
# ## 3. 季节性分析

# %%
# 按月汇总平均模式
df['month_of_year'] = df['order_purchase_timestamp'].dt.month
seasonal = df.groupby('month_of_year').agg(
    orders=('order_id', 'count'),
    revenue=('total_amount', 'sum'),
    avg_order_value=('total_amount', 'mean')
).reset_index()

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
seasonal['month_name'] = seasonal['month_of_year'].apply(lambda x: month_names[x-1])

# 计算季节性指数
seasonal['seasonal_index'] = seasonal['revenue'] / seasonal['revenue'].mean()

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# 月度模式
axes[0].bar(seasonal['month_of_year'], seasonal['orders'] / 1000, color='#42A5F5', edgecolor='white')
axes[0].set_xticks(range(1, 13))
axes[0].set_xticklabels(month_names)
axes[0].set_title('Average Monthly Order Volume (Thousands)', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Orders (K)')

# 季节性指数
colors = ['#EF5350' if v < 1 else '#4CAF50' for v in seasonal['seasonal_index']]
axes[1].bar(seasonal['month_of_year'], seasonal['seasonal_index'], color=colors, edgecolor='white')
axes[1].axhline(1, color='black', linestyle='--', linewidth=2)
axes[1].set_xticks(range(1, 13))
axes[1].set_xticklabels(month_names)
axes[1].set_title('Seasonal Index (1.0 = Average)', fontsize=14, fontweight='bold')
# 标注高低
for i, row in seasonal.iterrows():
    if row['seasonal_index'] > 1.05 or row['seasonal_index'] < 0.95:
        axes[1].annotate(f"{row['seasonal_index']:.2f}", (row['month_of_year'], row['seasonal_index']),
                        textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('./images/02_seasonality.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 4. 地理分析：收入从哪里来？

# %%
# 各州表现
state_stats = df.groupby('customer_state').agg(
    orders=('order_id', 'count'),
    revenue=('total_amount', 'sum'),
    avg_order_value=('total_amount', 'mean'),
    unique_customers=('customer_unique_id', 'nunique')
).reset_index()

state_stats['revenue_pct'] = state_stats['revenue'] / state_stats['revenue'].sum() * 100
state_stats['revenue_per_capita'] = state_stats['revenue'] / state_stats['unique_customers']
state_stats = state_stats.sort_values('revenue', ascending=False)

print("📊 各州收入 TOP 10:")
state_stats.head(10)[['customer_state', 'orders', 'revenue', 'revenue_pct', 'unique_customers']]

# %%
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# TOP 15 州收入
top_states = state_stats.head(15)
axes[0].barh(range(len(top_states)), top_states['revenue'] / 1e6, color='#1565C0')
axes[0].set_yticks(range(len(top_states)))
axes[0].set_yticklabels(top_states['customer_state'])
axes[0].invert_yaxis()
axes[0].set_title('Top 15 States by Revenue', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Revenue (M BRL)')

# 集中度（帕累托）
state_stats['cum_pct'] = state_stats['revenue_pct'].cumsum()
axes[1].plot(range(1, len(state_stats) + 1), state_stats['cum_pct'], linewidth=2, color='#7B1FA2')
axes[1].axhline(80, color='red', linestyle='--', alpha=0.7, label='80% line')
axes[1].axvline((state_stats['cum_pct'] <= 80).sum(), color='red', linestyle='--', alpha=0.7)
axes[1].annotate(f"{(state_stats['cum_pct'] <= 80).sum()} states = 80% revenue",
                xy=((state_stats['cum_pct'] <= 80).sum(), 80),
                xytext=(15, 60), arrowprops=dict(arrowstyle='->'), fontsize=11)
axes[1].set_title('Revenue Concentration (Pareto)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Number of States')
axes[1].set_ylabel('Cumulative Revenue %')

# 客单价 TOP vs BOTTOM
state_stats_sorted = state_stats.sort_values('avg_order_value', ascending=False)
axes[2].barh(range(10), state_stats_sorted.head(10)['avg_order_value'], color='#2E7D32', label='Top 10')
axes[2].barh(range(len(state_stats_sorted) - 10, len(state_stats_sorted)),
             state_stats_sorted.tail(10)['avg_order_value'], color='#C62828', label='Bottom 10')
axes[2].set_yticks([])
axes[2].set_title('AOV: Top 10 vs Bottom 10 States', fontsize=13, fontweight='bold')
axes[2].set_xlabel('Avg Order Value (BRL)')
axes[2].legend()
axes[2].axvline(df['total_amount'].mean(), color='gray', linestyle='--', label='Overall AVG')

plt.tight_layout()
plt.savefig('./images/02_geography.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 5. 支付方式分析

# %%
# 关联支付详情
df_items = pd.read_csv('./data/olist_order_items_dataset.csv')
df_payments = pd.read_csv('./data/olist_order_payments_dataset.csv')

payment_agg = df_payments.groupby('order_id').agg(
    payment_type=('payment_type', lambda x: x.mode().iloc[0] if not x.mode().empty else 'unknown'),
    total_installments=('payment_installments', 'max'),
    total_payment=('payment_value', 'sum')
).reset_index()

df_pay = df.merge(payment_agg, on='order_id', how='inner')

# 支付方式分布
pay_stats = df_pay.groupby('payment_type').agg(
    orders=('order_id', 'count'),
    revenue=('total_amount', 'sum'),
    avg_order_value=('total_amount', 'mean'),
    avg_installments=('total_installments', 'mean')
).reset_index()
pay_stats['pct'] = pay_stats['orders'] / pay_stats['orders'].sum() * 100
pay_stats = pay_stats.sort_values('orders', ascending=False)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 支付方式份额
axes[0].pie(pay_stats['orders'], labels=pay_stats['payment_type'], autopct='%1.1f%%',
            colors=sns.color_palette('Set2'), startangle=90, explode=[0.05]*len(pay_stats))
axes[0].set_title('Payment Method Share', fontsize=13, fontweight='bold')

# 分期偏好
installment_dist = df_pay.groupby('total_installments').size().reset_index(name='count')
installment_dist = installment_dist[installment_dist['total_installments'] <= 12]
axes[1].bar(installment_dist['total_installments'], installment_dist['count'] / 1000,
            color='#FFA726', edgecolor='white')
axes[1].set_title('Installment Distribution', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Number of Installments')
axes[1].set_ylabel('Orders (K)')

# 支付方式 vs 客单价
order = pay_stats.sort_values('avg_order_value', ascending=False)['payment_type'].tolist()
axes[2].bar(range(len(pay_stats)), pay_stats.set_index('payment_type').loc[order, 'avg_order_value'],
            color=['#1565C0' if t == 'credit_card' else '#90CAF9' for t in order])
axes[2].set_xticks(range(len(order)))
axes[2].set_xticklabels(order, rotation=30, ha='right')
axes[2].axhline(df_pay['total_amount'].mean(), color='red', linestyle='--', label=f'Overall AVG: R${df_pay["total_amount"].mean():.0f}')
axes[2].legend()
axes[2].set_title('AOV by Payment Method', fontsize=13, fontweight='bold')
axes[2].set_ylabel('Avg Order Value (BRL)')

plt.tight_layout()
plt.savefig('./images/02_payments.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 6. 时间节奏分析

# %%
# 一周中的哪一天
day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
day_stats = df.groupby('purchase_dayofweek').agg(
    orders=('order_id', 'count'),
    revenue=('total_amount', 'sum')
).reset_index()
day_stats['day_name'] = day_stats['purchase_dayofweek'].apply(lambda x: day_names[x])
day_stats['orders_pct'] = day_stats['orders'] / day_stats['orders'].sum() * 100

# 一天中的哪个小时
hour_stats = df.groupby('purchase_hour').agg(
    orders=('order_id', 'count'),
    revenue=('total_amount', 'sum')
).reset_index()

fig, axes = plt.subplots(1, 2, figsize=(16, 5))

axes[0].bar(day_stats['purchase_dayofweek'], day_stats['orders'] / 1000, color='#5C6BC0', edgecolor='white')
axes[0].set_xticks(range(7))
axes[0].set_xticklabels(day_names)
axes[0].set_title('Orders by Day of Week', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Orders (K)')
# 标注百分比
for i, row in day_stats.iterrows():
    axes[0].text(row['purchase_dayofweek'], row['orders']/1000 + 0.5,
                f"{row['orders_pct']:.1f}%", ha='center', fontsize=9)

axes[1].fill_between(hour_stats['purchase_hour'], hour_stats['orders'] / 1000,
                      alpha=0.3, color='#26A69A')
axes[1].plot(hour_stats['purchase_hour'], hour_stats['orders'] / 1000,
             marker='o', color='#00897B', linewidth=2)
axes[1].set_title('Orders by Hour of Day', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Hour')
axes[1].set_ylabel('Orders (K)')
axes[1].set_xticks(range(0, 24, 3))
# 标注高峰
peak_hour = hour_stats.loc[hour_stats['orders'].idxmax()]
axes[1].annotate(f"Peak: {int(peak_hour['purchase_hour'])}:00\n({peak_hour['orders']/1000:.1f}K orders)",
                xy=(peak_hour['purchase_hour'], peak_hour['orders']/1000),
                xytext=(peak_hour['purchase_hour'] + 4, peak_hour['orders']/1000 + 0.2),
                arrowprops=dict(arrowstyle='->', color='red'), fontsize=10, color='red')

plt.tight_layout()
plt.savefig('./images/02_time_patterns.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 7. 业务洞察总结

# %%
# 计算核心KPI
total_revenue = df['total_amount'].sum()
total_orders = len(df)
total_customers = df['customer_unique_id'].nunique()
aov = df['total_amount'].mean()

# 增长指标
df['purchase_month'] = df['order_purchase_timestamp'].dt.to_period('M')
first_6m = df[df['purchase_month'] <= df['purchase_month'].unique()[:6].max()]
last_6m = df[df['purchase_month'] >= df['purchase_month'].unique()[-6:].min()]
growth_rate = (last_6m['total_amount'].sum() / first_6m['total_amount'].sum() - 1) * 100

# TOP 州
top_3_states = state_stats.head(3)['customer_state'].tolist()

print(f"""
============================================================
📊 销售趋势与业务分析 — 核心发现
============================================================

📈 增长概览:
   - 总营收: R$ {total_revenue:,.0f}
   - 总订单: {total_orders:,}
   - 客单价均值: R$ {aov:,.0f}
   - 首末半年度增长率: {growth_rate:.1f}%

🌍 地域特征:
   - TOP 3 州: {', '.join(top_3_states)} (贡献 {state_stats.head(3)["revenue_pct"].sum():.1f}% 营收)
   - {(state_stats['cum_pct'] <= 80).sum()} 个州贡献了 80% 收入

💳 支付行为:
   - 信用卡主导 ({pay_stats.loc[pay_stats['payment_type'] == 'credit_card', 'pct'].values[0]:.1f}%)
   - 分期用户客单价是全额支付的 {pay_stats[pay_stats['payment_type']=='credit_card']['avg_order_value'].values[0] / df_pay['total_amount'].mean():.1f} 倍

⏰ 时间节奏:
   - 销售高峰: {day_names[day_stats['orders'].idxmax()]} ({day_stats['orders'].max()/1000:.1f}K 单/天)
   - 下单高峰: {int(peak_hour['purchase_hour'])}:00 ({peak_hour['orders']/1000:.1f}K 单)
   - 增长趋势: {'强劲上升' if growth_rate > 50 else '温和增长' if growth_rate > 20 else '平稳'}

🎯 业务建议:
   1. 在销售高峰州 (SP, RJ, MG) 加强仓储物流布局
   2. 信用卡+分期推广可提升客单价
   3. 工作日 + 10-22点覆盖最密集的下单窗口
============================================================
""")
