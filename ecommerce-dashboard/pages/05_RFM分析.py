"""
ShopEasy 运营看板 - Page 5: RFM 用户分层

展示用户价值分层、各分群画像、收入贡献分析。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import load_user_rfm
from utils.charts import (
    kpi_card, bar_chart, pie_chart, scatter_chart, COLOR_SEQUENCE,
)

st.set_page_config(page_title="RFM 分析", page_icon="🎯", layout="wide")

st.title("🎯 RFM 用户分层")
st.markdown("*基于 Recency(最近) / Frequency(频率) / Monetary(金额) 的用户价值分层*")

# ---- 加载数据 ----
with st.spinner("加载数据中..."):
    rfm = load_user_rfm()

# ---- RFM 概览 ----
st.markdown("### 分层概览")

segment_summary = rfm.groupby("rfm_segment").agg(
    user_count=("user_id", "count"),
    avg_recency=("recency", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_monetary=("monetary", "mean"),
    total_monetary=("monetary", "sum"),
).reset_index()

segment_summary["user_share"] = segment_summary["user_count"] / segment_summary["user_count"].sum() * 100
segment_summary["revenue_share"] = segment_summary["total_monetary"] / segment_summary["total_monetary"].sum() * 100

total_users = len(rfm)
total_revenue = rfm["monetary"].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(kpi_card("总用户数", f"{total_users:,}"), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card("累计消费", f"¥{total_revenue/10000:.0f}万"), unsafe_allow_html=True)
with col3:
    avg_freq = rfm["frequency"].mean()
    st.markdown(kpi_card("人均购买次数", f"{avg_freq:.1f}"), unsafe_allow_html=True)
with col4:
    vip_count = len(rfm[rfm["rfm_segment"] == "重要价值用户"])
    st.markdown(kpi_card("重要价值用户", f"{vip_count:,}"), unsafe_allow_html=True)

st.markdown("---")

# ---- 分层可视化 ----
col_left, col_right = st.columns(2)

with col_left:
    # 用户分布饼图
    fig = px.pie(
        segment_summary, names="rfm_segment", values="user_count",
        title="用户分层占比",
        color_discrete_sequence=COLOR_SEQUENCE, hole=0.4,
    )
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # 收入贡献 vs 用户占比
    comp_data = segment_summary[["rfm_segment", "user_share", "revenue_share"]].copy()
    comp_data = comp_data.melt(
        id_vars="rfm_segment", var_name="type", value_name="share"
    )
    comp_data["type"] = comp_data["type"].replace({
        "user_share": "用户占比", "revenue_share": "收入占比"
    })

    fig = px.bar(
        comp_data, x="rfm_segment", y="share", color="type",
        title="各分群用户占比 vs 收入贡献",
        barmode="group",
        color_discrete_sequence=["#3498db", "#e94560"],
    )
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

# ---- 分层详情表格 ----
st.markdown("### 分层画像明细")

segment_display = segment_summary.copy()
segment_display["avg_recency"] = segment_display["avg_recency"].round(1)
segment_display["avg_frequency"] = segment_display["avg_frequency"].round(1)
segment_display["avg_monetary"] = segment_display["avg_monetary"].round(0)
segment_display["user_share"] = segment_display["user_share"].round(1)
segment_display["revenue_share"] = segment_display["revenue_share"].round(1)

segment_display.columns = [
    "用户分层", "用户数", "平均R(天)", "平均F(次)", "平均M(¥)",
    "累计M(¥)", "用户占比(%)", "收入占比(%)"
]

# 按 用户数 排序
segment_display = segment_display.sort_values("用户数", ascending=False)

st.dataframe(
    segment_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "平均M(¥)": st.column_config.NumberColumn(format="¥%.0f"),
        "累计M(¥)": st.column_config.NumberColumn(format="¥%.0f"),
    },
)

st.markdown("---")

# ---- RFM 分布直方图 ----
st.markdown("### R/F/M 分布")
col1, col2, col3 = st.columns(3)

with col1:
    fig = px.histogram(
        rfm, x="recency", nbins=30, title="Recency 分布（天）",
        color_discrete_sequence=[COLOR_SEQUENCE[1]],
    )
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.histogram(
        rfm, x="frequency", nbins=20, title="Frequency 分布（次）",
        color_discrete_sequence=[COLOR_SEQUENCE[3]],
    )
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col3:
    fig = px.histogram(
        rfm, x="monetary", nbins=30, title="Monetary 分布（¥）",
        color_discrete_sequence=[COLOR_SEQUENCE[4]],
    )
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ---- RFM 散点图 ----
st.markdown("### RFM 三维交叉分析")
fig = px.scatter(
    rfm.sample(min(2000, len(rfm))),  # 采样以提升性能
    x="frequency", y="monetary", color="rfm_segment",
    size="recency", title="用户价值分布（气泡大小=Recency）",
    color_discrete_sequence=COLOR_SEQUENCE,
    hover_data=["recency"],
)
fig.update_layout(height=450, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)
