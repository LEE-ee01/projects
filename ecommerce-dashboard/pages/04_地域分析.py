"""
ShopEasy 运营看板 - Page 4: 地域分析

展示城市收入排名、增长分析、城市层级对比。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import load_city_performance
from utils.charts import (
    kpi_card, bar_chart, scatter_chart, COLOR_SEQUENCE,
)

st.set_page_config(page_title="地域分析", page_icon="🗺️", layout="wide")

st.title("🗺️ 地域分析")
st.markdown("*城市级别收入分布、增长趋势与城市层级对比*")

# ---- 加载数据 ----
with st.spinner("加载数据中..."):
    city = load_city_performance()

# 城市层级分类
TIER1 = ["北京", "上海", "广州", "深圳"]
TIER2 = ["杭州", "成都", "武汉", "南京", "重庆", "西安", "长沙", "苏州", "天津", "郑州"]

city["city_tier"] = city["city"].apply(
    lambda c: "一线城市" if c in TIER1 else ("二线城市" if c in TIER2 else "三线城市")
)

# ---- 城市概览 ----
st.markdown("### 城市业绩总览")

city_total = city.groupby("city").agg(
    total_revenue=("revenue", "sum"),
    total_orders=("order_count", "sum"),
    total_buyers=("unique_buyers", "sum"),
    avg_aov=("avg_aov", "mean"),
).reset_index()

top_city = city_total.nlargest(1, "total_revenue").iloc[0]
n_cities = city_total["city"].nunique()
total_revenue_all = city_total["total_revenue"].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(kpi_card("覆盖城市", f"{n_cities}"), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card("累计收入", f"¥{total_revenue_all/10000:.0f}万"), unsafe_allow_html=True)
with col3:
    st.markdown(kpi_card("Top 城市", top_city["city"]), unsafe_allow_html=True)
with col4:
    top_share = top_city["total_revenue"] / total_revenue_all * 100 if total_revenue_all > 0 else 0
    st.markdown(kpi_card("Top 城市份额", f"{top_share:.1f}%"), unsafe_allow_html=True)

st.markdown("---")

# ---- 城市排名 ----
st.markdown("### 城市收入排名")
top_n = st.slider("显示前 N 名城市", 5, 34, 15)

col_left, col_right = st.columns(2)

with col_left:
    top_cities = city_total.nlargest(top_n, "total_revenue")
    fig = px.bar(
        top_cities.sort_values("total_revenue", ascending=True),
        x="total_revenue", y="city", orientation='h',
        title=f"Top {top_n} 城市收入",
        color="total_revenue",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # 城市增长散点图
    latest_month = city["order_month"].max()
    prev_month = latest_month - pd.DateOffset(months=1)

    city_latest = city[city["order_month"] == latest_month][["city", "revenue", "city_tier"]].rename(
        columns={"revenue": "revenue_current"}
    )
    city_prev = city[city["order_month"] == prev_month][["city", "revenue"]].rename(
        columns={"revenue": "revenue_prev"}
    )

    city_growth = city_latest.merge(city_prev, on="city", how="left")
    city_growth["mom_growth"] = (
        (city_growth["revenue_current"] - city_growth["revenue_prev"])
        / city_growth["revenue_prev"] * 100
    )

    fig = px.scatter(
        city_growth.dropna(),
        x="revenue_current", y="mom_growth",
        color="city_tier", text="city",
        title="城市收入 vs 环比增长",
        color_discrete_sequence=["#e94560", "#16a085", "#3498db"],
    )
    fig.update_traces(textposition='top center', marker=dict(size=10))
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---- 城市层级对比 ----
st.markdown("### 城市层级对比")

tier_summary = city.groupby(["order_month", "city_tier"]).agg(
    revenue=("revenue", "sum"),
    orders=("order_count", "sum"),
    buyers=("unique_buyers", "sum"),
).reset_index()

col_left, col_right = st.columns(2)

with col_left:
    fig = px.area(
        tier_summary, x="order_month", y="revenue", color="city_tier",
        title="各层级城市月度收入趋势",
        color_discrete_sequence=["#e94560", "#16a085", "#3498db"],
    )
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    tier_total = city.groupby("city_tier").agg(
        revenue=("revenue", "sum"),
        cities=("city", "nunique"),
    ).reset_index()
    tier_total["revenue_per_city"] = tier_total["revenue"] / tier_total["cities"]

    fig = px.bar(
        tier_total, x="city_tier", y="revenue_per_city",
        title="各层级单城市均收入 (¥)",
        color="city_tier",
        color_discrete_sequence=["#e94560", "#16a085", "#3498db"],
        text_auto='.0f',
    )
    fig.update_layout(showlegend=False, height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
