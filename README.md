# Data Analyst Portfolio

> 从商业理解到数据洞察，用数据驱动业务决策。

6 个数据分析项目，覆盖电商全链路分析、数据仓库 ETL、交互看板、机器学习与统计推断。

---

## 项目导航

| # | 项目 | 技术栈 | 简介 |
|---|------|--------|------|
| 1 | [Olist 电商分析](cc/olist-ecommerce-analysis/) | Python · SQLite · Pandas | 9 表关联 100K+ 订单，RFM / Cohort / SQL |
| 2 | [电商数据仓库](ecommerce-dw/) | Python · DuckDB · SQL | ODS→DWD→DWS→ADS 四层架构，10 张指标表 |
| 3 | [电商运营看板](ecommerce-dashboard/) | Streamlit · Plotly | 5 页交互看板，15+ 种可视化图表 |
| 4 | [水军检测系统](网络水军/) | Python · BERT · XGBoost | 8 步 ML Pipeline，F1 0.84，AUC 0.976 |
| 5 | [A/B 测试分析](ab-test-analysis/) | SciPy · Statsmodels | Z 检验 · Bootstrap · 分层分析 · 业务决策 |
| 6 | [财务管理系统](demo2/) | Java · Spring Boot · MySQL | 复式记账，13 个 REST API，三大财务报表 |

---

## 作品集网页

打开 [`portfolio.html`](portfolio.html) 即可在浏览器中查看交互式作品集。

---

## 技能概览

| 类别 | 技能 |
|------|------|
| 数据分析 | Python · Pandas · NumPy · SQL · Jupyter · SciPy |
| 数据工程 | DuckDB · ETL · 数据仓库建模 · 数据质量监控 |
| 机器学习 | Scikit-learn · XGBoost · LightGBM · BERT · SHAP |
| 可视化 | Streamlit · Plotly · Matplotlib · Seaborn |
| 统计方法 | 假设检验 · Bootstrap · A/B Testing · 效应量 |
| 后端 | Spring Boot · MyBatis · MySQL · RESTful API |

---

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/LEE-ee01/projects.git
cd projects

# 数据仓库项目
cd ecommerce-dw
pip install -r requirements.txt
python scripts/00_generate_data.py
python scripts/01_ods_load.py
# ... 依次运行 01-06

# 运营看板
cd ../ecommerce-dashboard
pip install -r requirements.txt
streamlit run app.py
```

---

## 联系方式

- **GitHub**: [github.com/LEE-ee01](https://github.com/LEE-ee01)
- **Email**: 2398083453@qq.com
