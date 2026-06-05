"""
ShopEasy 运营看板 - Page 2: 用户分析

展示新老客占比、留存热力图、会员等级消费分析。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data_loader import (
    load_daily_kpi, load_user_cohort, load_membership_analysis, load_user_rfm,
)
from utils.charts import (
    kpi_card, bar_chart, pie_chart, retention_heatmap, scatter_chart,
    apply_common_layout, COLOR_SEQUENCE,
)

st.set_page_config(page_title="用户分析", page_icon="👤", layout="wide")

st.title("👤 用户分析")
st.markdown("*用户行为、留存与价值分析*")

# ---- 加载数据 ----
with st.spinner("加载数据中..."):
    daily = load_daily_kpi()
    cohort = load_user_cohort()
    membership = load_membership_analysis()
    rfm = load_user_rfm()

# ---- 用户概览 KPI ----
st.markdown("### 用户概览")

# 新客 vs 老客（简化计算）
daily["order_month"] = daily["order_date"].dt.to_period("M")
monthly_buyers = daily.groupby("order_month")["unique_buyers"].sum()
avg_monthly_buyers = monthly_buyers.mean()

total_users = len(rfm)
active_users = len(rfm[rfm["recency"] <= 30])
repurchase_users = len(rfm[rfm["frequency"] >= 2])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(kpi_card("总用户数", f"{total_users:,}"), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card("月均活跃用户", f"{avg_monthly_buyers:,.0f}"), unsafe_allow_html=True)
with col3:
    st.markdown(kpi_card("近30天活跃", f"{active_users:,}"), unsafe_allow_html=True)
with col4:
    repurchase_rate = repurchase_users / total_users * 100 if total_users > 0 else 0
    st.markdown(kpi_card("复购率", f"{repurchase_rate:.1f}%"), unsafe_allow_html=True)

st.markdown("---")

# ---- 留存热力图 ----
st.markdown("### 用户留存分析（周度 Cohort）")

if not cohort.empty:
    # 选择最近的几个 Cohort
    latest_cohorts = cohort["cohort_week"].drop_duplicates().nlargest(8)
    cohort_filtered = cohort[cohort["cohort_week"].isin(latest_cohorts)]

    pivot = cohort_filtered.pivot_table(
        values="retention_rate", index="cohort_week", columns="week_number", aggfunc="mean"
    )

    fig = px.imshow(
        pivot * 100,
        title="周度留存率 (%)",
        aspect="auto",
        color_continuous_scale="RdYlGn",
        labels=dict(x="周数", y="注册周", color="留存率(%)"),
    )
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---- 会员分析 ----
st.markdown("### 会员等级消费分析")

col_left, col_right = st.columns(2)

with col_left:
    # 会员人数分布
    membership_summary = membership.groupby("membership_level").agg(
        total_revenue=("total_revenue", "sum"),
        unique_buyers=("unique_buyers", "sum"),
        avg_arpu=("arpu", "mean"),
    ).reset_index()

    fig = px.pie(
        membership_summary, names="membership_level", values="unique_buyers",
        title="会员人数分布",
        color_discrete_sequence=COLOR_SEQUENCE,
        hole=0.4,
    )
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # ARPU 对比
    fig = px.bar(
        membership_summary.sort_values("avg_arpu", ascending=True),
        x="avg_arpu", y="membership_level",
        orientation='h', title="各等级 ARPU (¥)",
        color="membership_level",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(showlegend=False, height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

# 会员月度趋势
st.markdown("#### 会员月度收入趋势")
monthly_membership = membership.groupby(["order_month", "membership_level"])["total_revenue"].sum().reset_index()
fig = px.area(
    monthly_membership, x="order_month", y="total_revenue",
    color="membership_level", title="各等级月度收入贡献",
    color_discrete_sequence=COLOR_SEQUENCE,
)
fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)
