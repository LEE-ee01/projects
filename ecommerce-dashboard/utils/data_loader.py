"""
ShopEasy 运营看板 - 数据加载模块

从 DW 项目输出的 CSV 报表中加载数据，并缓存以提高性能。
"""

import pandas as pd
from pathlib import Path
import streamlit as st

# DW 项目输出目录
DW_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "ecommerce-dw" / "output" / "reports"


@st.cache_data(ttl=3600)
def load_daily_kpi() -> pd.DataFrame:
    """加载每日 KPI 数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_daily_kpi.csv")
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df


@st.cache_data(ttl=3600)
def load_user_cohort() -> pd.DataFrame:
    """加载用户留存数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_user_cohort.csv")
    df["cohort_week"] = pd.to_datetime(df["cohort_week"])
    return df


@st.cache_data(ttl=3600)
def load_category_ranking() -> pd.DataFrame:
    """加载品类排名数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_category_ranking.csv")
    df["order_month"] = pd.to_datetime(df["order_month"])
    return df


@st.cache_data(ttl=3600)
def load_city_performance() -> pd.DataFrame:
    """加载城市业绩数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_city_performance.csv")
    df["order_month"] = pd.to_datetime(df["order_month"])
    return df


@st.cache_data(ttl=3600)
def load_membership_analysis() -> pd.DataFrame:
    """加载会员分析数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_membership_analysis.csv")
    df["order_month"] = pd.to_datetime(df["order_month"])
    return df


@st.cache_data(ttl=3600)
def load_hourly_traffic() -> pd.DataFrame:
    """加载时段流量数据。"""
    return pd.read_csv(DW_REPORTS_DIR / "ads_hourly_traffic.csv")


@st.cache_data(ttl=3600)
def load_brand_share() -> pd.DataFrame:
    """加载品牌份额数据。"""
    return pd.read_csv(DW_REPORTS_DIR / "ads_brand_share.csv")


@st.cache_data(ttl=3600)
def load_discount_effectiveness() -> pd.DataFrame:
    """加载折扣效果数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_discount_effectiveness.csv")
    df["order_month"] = pd.to_datetime(df["order_month"])
    return df


@st.cache_data(ttl=3600)
def load_user_rfm() -> pd.DataFrame:
    """加载用户 RFM 数据。"""
    return pd.read_csv(DW_REPORTS_DIR / "ads_user_rfm.csv")


@st.cache_data(ttl=3600)
def load_monthly_summary() -> pd.DataFrame:
    """加载月度汇总数据。"""
    df = pd.read_csv(DW_REPORTS_DIR / "ads_monthly_summary.csv")
    df["order_month"] = pd.to_datetime(df["order_month"])
    return df


def check_data_available() -> bool:
    """检查 DW 项目输出数据是否可用。"""
    required_files = [
        "ads_daily_kpi.csv",
        "ads_user_rfm.csv",
        "ads_monthly_summary.csv",
        "ads_category_ranking.csv",
        "ads_city_performance.csv",
    ]
    for f in required_files:
        if not (DW_REPORTS_DIR / f).exists():
            return False
    return True
