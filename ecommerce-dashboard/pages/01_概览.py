"""
ShopEasy 运营看板 - Page 1: 经营概览

展示核心 KPI 卡片、GMV 日度趋势、品类收入 treemap、时段流量分布。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import (
    load_daily_kpi, load_category_ranking, load_hourly_traffic, load_monthly_summary,
)
from utils.charts import (
    kpi_card, daily_trend_chart, treemap_chart, bar_chart, pie_chart,
    COLOR_SEQUENCE,
)

st.set_page_config(page_title="经营概览", page_icon="📈", layout="wide")

st.title("📈 经营概览")
st.markdown("*核心经营指标一览 — ShopEasy 电商平台*")

# ---- 加载数据 ----
with st.spinner("加载数据中..."):
    daily = load_daily_kpi()
    category = load_category_ranking()
    hourly = load_hourly_traffic()
    monthly = load_monthly_summary()

# ---- 日期筛选 ----
min_date = daily["order_date"].min().date()
max_date = daily["order_date"].max().date()
date_range = st.date_input(
    "选择日期范围",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if len(date_range) == 2:
    start_date, end_date = date_range
    daily_filtered = daily[
        (daily["order_date"] >= pd.Timestamp(start_date)) &
        (daily["order_date"] <= pd.Timestamp(end_date))
    ]
else:
    daily_filtered = daily

# ---- KPI 卡片 ----
st.markdown("### 核心指标")
total_gmv = daily_filtered["gmv"].sum()
total_orders = daily_filtered["order_count"].sum()
total_buyers = daily_filtered["unique_buyers"].sum()
avg_aov = daily_filtered["aov"].mean()
total_discount = daily_filtered["total_discount"].sum()

# 计算环比（与前一周期对比）
days_in_range = len(daily_filtered)
prev_start = pd.Timestamp(start_date) - pd.Timedelta(days=days_in_range) if len(date_range) == 2 else None

if prev_start is not None and len(date_range) == 2:
    prev_end = pd.Timestamp(start_date) - pd.Timedelta(days=1)
    prev_data = daily[(daily["order_date"] >= prev_start) & (daily["order_date"] <= prev_end)]
    if len(prev_data) > 0:
        gmv_change = (total_gmv - prev_data["gmv"].sum()) / prev_data["gmv"].sum() * 100
        gmv_delta = f"{'↑' if gmv_change > 0 else '↓'}{abs(gmv_change):.1f}%"
    else:
        gmv_delta = ""
else:
    gmv_delta = ""

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(kpi_card("累计 GMV", f"¥{total_gmv/10000:.0f}万", gmv_delta), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card("订单数", f"{total_orders:,}"), unsafe_allow_html=True)
with col3:
    st.markdown(kpi_card("下单用户数", f"{total_buyers:,}"), unsafe_allow_html=True)
with col4:
    st.markdown(kpi_card("平均客单价", f"¥{avg_aov:.0f}"), unsafe_allow_html=True)
with col5:
    discount_rate = total_discount / (total_gmv + total_discount) * 100 if (total_gmv + total_discount) > 0 else 0
    st.markdown(kpi_card("折扣率", f"{discount_rate:.1f}%"), unsafe_allow_html=True)

st.markdown("---")

# ---- 日度 GMV 趋势 ----
st.markdown("### 日度 GMV 趋势")
fig = daily_trend_chart(daily_filtered, metrics=["gmv"])
fig.update_layout(height=350)
st.plotly_chart(fig, use_container_width=True)

# ---- 品类结构 & 时段分布 ----
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 品类收入占比")
    latest_month = category["order_month"].max()
    cat_latest = category[category["order_month"] == latest_month]
    cat_summary = cat_latest.groupby("category_l1")["revenue"].sum().reset_index()
    fig = px.treemap(
        cat_summary, path=["category_l1"], values="revenue",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=350)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("### 时段订单分布")
    if not hourly.empty:
        period_order = hourly.groupby("time_period")["order_count"].sum().reset_index()
        period_order = period_order.sort_values("order_count", ascending=True)
        fig = px.bar(
            period_order, x="order_count", y="time_period",
            orientation='h', color="time_period",
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("时段数据不足")

# ---- 月度 GMV 趋势 ----
st.markdown("### 月度 GMV 与环比增长")
col1, col2 = st.columns([2, 1])

with col1:
    fig = px.bar(
        monthly, x="order_month", y="gmv",
        title="月度 GMV",
        color_discrete_sequence=[COLOR_SEQUENCE[0]],
    )
    fig.add_trace(
        px.line(monthly, x="order_month", y="gmv").data[0]
    )
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    monthly_display = monthly[["order_month", "gmv", "gmv_mom", "gmv_yoy"]].copy()
    monthly_display["gmv"] = monthly_display["gmv"].apply(lambda x: f"¥{x/10000:.0f}万")
    monthly_display["gmv_mom"] = monthly_display["gmv_mom"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "-"
    )
    monthly_display["gmv_yoy"] = monthly_display["gmv_yoy"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "-"
    )
    monthly_display.columns = ["月份", "GMV", "环比", "同比"]
    st.dataframe(
        monthly_display.sort_values("月份", ascending=False),
        use_container_width=True, hide_index=True, height=350,
    )
