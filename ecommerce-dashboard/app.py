"""
ShopEasy 运营看板 - 主入口

多页面 Streamlit 应用，连接 DW 项目输出的 ADS 数据表，
提供交互式电商运营数据分析看板。
"""

import streamlit as st

# 页面配置（必须在其他 st 调用之前）
st.set_page_config(
    page_title="ShopEasy 运营看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 主页面 — 重定向到概览页
# ============================================================

st.markdown("""
# 📊 ShopEasy 电商运营看板

欢迎使用 ShopEasy 电商数据运营看板。请从左侧导航栏选择一个分析页面。

---

### 📄 分析页面

| 页面 | 说明 |
|------|------|
| 📈 **经营概览** | 核心 KPI、日度趋势、品类结构、时段分析 |
| 👤 **用户分析** | 新老客占比、留存热力图、会员消费分析 |
| 🛍️ **商品分析** | 品类排名、品牌份额、折扣效果 |
| 🗺️ **地域分析** | 城市收入排名、增长分析、城市层级对比 |
| 🎯 **RFM 分析** | 用户价值分层、分群画像、收入贡献 |

### 📊 数据来源

数据来自 **ShopEasy 电商数据仓库** 项目的 ADS 层输出（10 张业务指标表），
经过 ODS → DWD → DWS → ADS 四层 ETL 流程处理。

---

*使用左侧边栏导航或下方按钮选择分析页面。*
""")

# 侧边栏：项目信息
with st.sidebar:
    st.markdown("## 📊 ShopEasy 看板")
    st.markdown("---")
    st.markdown("**数据来源**: 电商数据仓库 ADS 层")
    st.markdown("**数据范围**: 2024-01 ~ 2025-12")
    st.markdown("**技术栈**: Streamlit + Plotly + DuckDB")
    st.markdown("---")
    st.markdown("*Made by 李欣昱*")
