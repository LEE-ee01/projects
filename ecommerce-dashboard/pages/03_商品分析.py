"""
ShopEasy 运营看板 - Page 3: 商品分析

展示品类排名、品牌份额、折扣效果分析。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data_loader import (
    load_category_ranking, load_brand_share, load_discount_effectiveness,
)
from utils.charts import (
    kpi_card, bar_chart, pie_chart, treemap_chart, COLOR_SEQUENCE,
)

st.set_page_config(page_title="商品分析", page_icon="🛍️", layout="wide")

st.title("🛍️ 商品分析")
st.markdown("*品类表现、品牌竞争格局与折扣策略效果*")

# ---- 加载数据 ----
with st.spinner("加载数据中..."):
    category = load_category_ranking()
    brand = load_brand_share()
    discount = load_discount_effectiveness()

# ---- 品类筛选 ----
all_categories = sorted(category["category_l1"].unique())
selected_category = st.selectbox("选择一级品类", ["全部"] + all_categories)

if selected_category != "全部":
    category = category[category["category_l1"] == selected_category]
    brand = brand[brand["category_l1"] == selected_category]

latest_month = category["order_month"].max()

# ---- KPI 行 ----
st.markdown("### 品类概况")
cat_latest = category[category["order_month"] == latest_month]
total_cat_revenue = cat_latest["revenue"].sum()
total_cat_orders = cat_latest["order_count"].sum()
n_active_cats = cat_latest["category_l2"].nunique()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(kpi_card(f"月度品类收入", f"¥{total_cat_revenue/10000:.0f}万"), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card(f"月度品类订单", f"{total_cat_orders:,}"), unsafe_allow_html=True)
with col3:
    st.markdown(kpi_card(f"活跃二级品类", f"{n_active_cats}"), unsafe_allow_html=True)

st.markdown("---")

# ---- 品类排名 ----
st.markdown("### 品类收入排名")

col_left, col_right = st.columns(2)

with col_left:
    # Top 10 二级品类
    top_cats = cat_latest.nlargest(10, "revenue")
    fig = px.bar(
        top_cats.sort_values("revenue", ascending=True),
        x="revenue", y="category_l2",
        orientation='h', title=f"Top 10 二级品类收入（{str(latest_month)[:7]}）",
        color="category_l1",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(showlegend=True, height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # 品类收入 treemap
    cat_summary = cat_latest.groupby("category_l1")["revenue"].sum().reset_index()
    fig = px.treemap(
        cat_summary, path=["category_l1"], values="revenue",
        title="一级品类收入占比",
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

# 品类趋势
st.markdown("#### 一级品类月度收入趋势")
cat_monthly = category.groupby(["order_month", "category_l1"])["revenue"].sum().reset_index()
fig = px.area(
    cat_monthly, x="order_month", y="revenue", color="category_l1",
    title="各品类月度收入走势",
    color_discrete_sequence=COLOR_SEQUENCE,
)
fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---- 品牌份额 ----
st.markdown("### 品牌竞争格局")

if not brand.empty:
    # Top 品牌
    brand_summary = brand.groupby("brand").agg(
        brand_revenue=("brand_revenue", "sum"),
        brand_orders=("brand_orders", "sum"),
    ).reset_index()

    top_brands = brand_summary.nlargest(15, "brand_revenue")

    col_left, col_right = st.columns(2)
    with col_left:
        fig = px.bar(
            top_brands.sort_values("brand_revenue", ascending=True),
            x="brand_revenue", y="brand", orientation='h',
            title="Top 15 品牌收入",
            color_discrete_sequence=[COLOR_SEQUENCE[0]],
        )
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig = px.pie(
            top_brands, names="brand", values="brand_revenue",
            title="Top 15 品牌收入份额",
            color_discrete_sequence=COLOR_SEQUENCE, hole=0.4,
        )
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---- 折扣效果 ----
st.markdown("### 折扣策略效果")

if not discount.empty:
    discount_summary = discount.groupby("discount_bucket").agg(
        total_orders=("order_count", "sum"),
        total_revenue=("total_revenue", "sum"),
        avg_aov=("avg_order_value", "mean"),
    ).reset_index()

    col_left, col_right = st.columns(2)

    with col_left:
        fig = px.bar(
            discount_summary, x="discount_bucket", y="total_orders",
            title="各折扣区间订单数",
            color="discount_bucket",
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        fig.update_layout(showlegend=False, height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        fig = px.bar(
            discount_summary, x="discount_bucket", y="avg_aov",
            title="各折扣区间平均客单价 (¥)",
            color="discount_bucket",
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        fig.update_layout(showlegend=False, height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
