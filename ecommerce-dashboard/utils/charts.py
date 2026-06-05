"""
ShopEasy 运营看板 - 图表组件模块

提供各页面复用的 Plotly 图表生成函数。
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 统一的颜色主题
COLORS = {
    "primary": "#1a1a2e",
    "accent": "#e94560",
    "blue": "#0f3460",
    "teal": "#16a085",
    "orange": "#e67e22",
    "purple": "#8e44ad",
    "green": "#27ae60",
    "red": "#e74c3c",
}

COLOR_SEQUENCE = ["#1a1a2e", "#e94560", "#0f3460", "#16a085", "#e67e22",
                   "#8e44ad", "#27ae60", "#e74c3c", "#3498db", "#f39c12"]

# 统一的 Plotly 布局设置
def apply_common_layout(fig, title: str, x_title: str = "", y_title: str = ""):
    """应用统一的图表布局风格。"""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=COLORS["primary"])),
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        font=dict(family="PingFang SC, Microsoft YaHei, sans-serif"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
    )
    return fig


def kpi_card(label: str, value: str, delta: str = "", delta_color: str = "normal"):
    """
    创建 KPI 卡片（返回 HTML 字符串用于 st.markdown）。

    Args:
        label: 指标名称
        value: 指标值
        delta: 变化值
        delta_color: "normal"或"inverse"
    """
    delta_html = ""
    if delta:
        color = "#27ae60" if "↑" in delta else "#e74c3c" if "↓" in delta else "#666"
        delta_html = f'<span style="color:{color};font-size:0.9rem;">{delta}</span>'

    return f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #eee;
    ">
        <div style="color: #888; font-size: 0.85rem; margin-bottom: 8px;">{label}</div>
        <div style="font-size: 1.6rem; font-weight: 700; color: #1a1a2e;">{value}</div>
        <div style="margin-top: 4px;">{delta_html}</div>
    </div>
    """


def daily_trend_chart(df: pd.DataFrame, date_col: str = "order_date",
                      metrics: list = None, title: str = "日度趋势") -> go.Figure:
    """日度趋势折线图。"""
    if metrics is None:
        metrics = ["gmv"]

    fig = go.Figure()
    for m in metrics:
        display_name = {"gmv": "GMV", "order_count": "订单数",
                        "unique_buyers": "下单用户", "aov": "客单价"}.get(m, m)
        fig.add_trace(go.Scatter(
            x=df[date_col], y=df[m], mode="lines",
            name=display_name,
            line=dict(width=2),
            hovertemplate=f"{display_name}: %{{y:,.0f}}<extra></extra>"
        ))

    apply_common_layout(fig, title)
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "",
              color: str = None, horizontal: bool = True,
              top_n: int = None) -> go.Figure:
    """通用柱状图。"""
    data = df.nlargest(top_n, y) if top_n else df

    if horizontal:
        fig = px.bar(data, x=y, y=x, orientation='h',
                      title=title, color=color,
                      color_discrete_sequence=COLOR_SEQUENCE)
    else:
        fig = px.bar(data, x=x, y=y, title=title, color=color,
                      color_discrete_sequence=COLOR_SEQUENCE)

    apply_common_layout(fig, title)
    return fig


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str = "") -> go.Figure:
    """饼图 / 环形图。"""
    fig = px.pie(df, names=names, values=values, title=title,
                 color_discrete_sequence=COLOR_SEQUENCE, hole=0.4)
    apply_common_layout(fig, title)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig


def heatmap_chart(df: pd.DataFrame, x: str, y: str, z: str, title: str = "") -> go.Figure:
    """热力图。"""
    pivot = df.pivot_table(values=z, index=y, columns=x, aggfunc="sum")
    fig = px.imshow(pivot, title=title, aspect="auto",
                    color_continuous_scale="Reds")
    apply_common_layout(fig, title)
    return fig


def retention_heatmap(df: pd.DataFrame, title: str = "用户留存热力图") -> go.Figure:
    """留存率热力图。"""
    pivot = df.pivot_table(
        values="retention_rate", index="cohort_week", columns="week_number", aggfunc="mean"
    )
    # 格式化为百分比
    annot = pivot.map(lambda x: f"{x:.1%}" if pd.notna(x) else "")

    fig = px.imshow(
        pivot * 100, title=title, aspect="auto",
        color_continuous_scale="RdYlGn",
        labels=dict(x="周数", y="注册周", color="留存率(%)")
    )
    apply_common_layout(fig, title)
    return fig


def scatter_chart(df: pd.DataFrame, x: str, y: str, color: str = None,
                  size: str = None, title: str = "", text: str = None) -> go.Figure:
    """散点图。"""
    fig = px.scatter(df, x=x, y=y, color=color, size=size,
                     text=text, title=title,
                     color_discrete_sequence=COLOR_SEQUENCE)
    apply_common_layout(fig, title)
    if text:
        fig.update_traces(textposition='top center')
    return fig


def treemap_chart(df: pd.DataFrame, path: list, values: str, title: str = "") -> go.Figure:
    """矩形树图。"""
    fig = px.treemap(df, path=path, values=values, title=title,
                     color_discrete_sequence=COLOR_SEQUENCE)
    apply_common_layout(fig, title)
    return fig
