# ShopEasy 电商数据仓库

## 项目概述

基于 **DuckDB + Python** 构建的电商数据仓库 ETL 项目。以虚构电商平台 "ShopEasy" 为业务场景，实现从原始业务数据到分析报表的完整数据仓库流程。

**四层数据架构**：ODS（操作数据层）→ DWD（明细数据层）→ DWS（服务数据层）→ ADS（应用数据层）

## 业务背景

ShopEasy 是一家运营两年的中型电商平台，拥有 5,000+ 注册用户和 500+ SKU。数据团队需要搭建公司第一个数据仓库，支撑日常运营报表和高管决策看板。

## 技术架构

```
源系统 (CSV)  →  ODS 层  →  DWD 层  →  DWS 层  →  ADS 层  →  报表导出
   │               │          │          │           │            │
   │         原始数据入库  清洗/标准化   日度汇总    业务指标     CSV文件
   │                        派生字段    宽表构建    窗口函数     Streamlit
   │                        空值处理                RFM分层      看板
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.x |
| 数据库 | DuckDB（嵌入式 OLAP 引擎） |
| 数据处理 | Pandas, NumPy, PyArrow |
| 配置管理 | PyYAML |
| 数据格式 | CSV (源) → Parquet (中间层) → CSV (输出) |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成模拟数据
python scripts/00_generate_data.py

# 3. 依次运行 ETL 流程
python scripts/01_ods_load.py      # ODS 层：数据入库
python scripts/02_dwd_process.py   # DWD 层：清洗标准化
python scripts/03_dws_aggregate.py # DWS 层：轻度汇总
python scripts/04_ads_build.py     # ADS 层：业务指标
python scripts/05_quality_check.py # 数据质量检查
python scripts/06_export_reports.py # 报表导出
```

## 项目结构

```
ecommerce-dw/
├── README.md                       # 项目说明
├── requirements.txt                # Python 依赖
├── config.yaml                     # 全局配置
│
├── scripts/                        # ETL 脚本
│   ├── utils.py                    # 公共工具模块
│   ├── 00_generate_data.py         # 模拟数据生成
│   ├── 01_ods_load.py              # ODS 层加载
│   ├── 02_dwd_process.py           # DWD 层清洗
│   ├── 03_dws_aggregate.py         # DWS 层汇总
│   ├── 04_ads_build.py             # ADS 层构建
│   ├── 05_quality_check.py         # 质量检查
│   └── 06_export_reports.py        # 报表导出
│
├── sql/                            # SQL 脚本
│   ├── 01_create_ods.sql           # ODS DDL
│   ├── 02_create_dwd.sql           # DWD DDL
│   ├── 03_create_dws.sql           # DWS DDL
│   ├── 04_create_ads.sql           # ADS DDL（10张指标表）
│   ├── 05_quality_checks.sql       # 质量检查 SQL
│   └── 06_business_queries.sql     # 15个业务分析查询
│
├── docs/                           # 文档
│   ├── data_dictionary.md          # 数据字典
│   ├── data_lineage.md             # 数据血缘
│   └── business_metrics.md         # 业务指标定义
│
├── data/                           # 数据文件（.gitignore）
│   ├── raw/                        # 源 CSV
│   ├── ods/, dwd/, dws/, ads/     # 各层 Parquet
│   └── shopeasy.duckdb            # DuckDB 数据库
│
└── output/                         # 输出
    ├── reports/                    # 导出的 10 张 CSV 报表
    ├── figures/                    # 可视化图表
    └── quality_report.txt          # 质量检查报告
```

## 核心成果

- **3 张源表**共 ~30,000 行业务数据（用户 5,000 / 商品 500 / 订单 25,000）
- **4 层数据仓库**，每层有独立 schema 和数据
- **10 张 ADS 业务指标表**：日度KPI、用户留存、品类排名、城市表现、会员分析、时段流量、品牌份额、折扣效果、RFM分层、月度汇总
- **15 个 SQL 业务分析查询**：覆盖趋势、对比、排名、分层、漏斗等多种分析场景
- **完整数据质量监控**：空值率、主键唯一性、参照完整性、业务逻辑检查
- **数据血缘文档**：清晰的上下游依赖关系

## 数据血缘

参见 [docs/data_lineage.md](docs/data_lineage.md)

## 业务指标定义

参见 [docs/business_metrics.md](docs/business_metrics.md)
