# ShopEasy 电商运营看板

## 项目概述

基于 **Streamlit + Plotly** 的交互式电商运营数据分析看板。以 ShopEasy 电商平台为业务场景，提供从经营概览到用户分层的 5 大分析模块。

数据来源于 [ShopEasy 电商数据仓库](../ecommerce-dw/) 项目的 ADS 层输出。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Streamlit |
| 可视化 | Plotly |
| 数据处理 | Pandas |
| 数据源 | DuckDB (通过 DW 项目 CSV 导出) |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保已运行 DW 项目并生成报表
# （如果尚未运行，请先执行 DW 项目中的 ETL 流程）

# 3. 启动看板
streamlit run app.py
```

## 页面结构

| 页面 | 内容 |
|------|------|
| 📈 **经营概览** | KPI 卡片、GMV 日度趋势、品类 treemap、时段分布 |
| 👤 **用户分析** | 新老客占比、留存热力图、会员等级消费分析 |
| 🛍️ **商品分析** | 品类排名、品牌份额、折扣效果分析 |
| 🗺️ **地域分析** | 城市收入排名、增长散点图、城市层级对比 |
| 🎯 **RFM 分析** | 用户价值分层、分群画像、收入贡献 |

## 交互功能

- 📅 日期范围筛选
- 🏷️ 品类下拉筛选
- 🔢 Top N 调节滑块
- 🎨 统一 Plotly 图表风格
- 📊 数据表格排序与导出

## 项目结构

```
ecommerce-dashboard/
├── README.md
├── requirements.txt
├── app.py                    # 主入口
├── pages/
│   ├── 01_概览.py
│   ├── 02_用户分析.py
│   ├── 03_商品分析.py
│   ├── 04_地域分析.py
│   └── 05_RFM分析.py
├── utils/
│   ├── data_loader.py        # 数据加载 + 缓存
│   └── charts.py             # 图表组件
└── screenshots/              # 页面截图
```
