# Olist 巴西电商数据分析

> 📊 基于 Olist Brazilian E-Commerce 数据集的完整数据分析项目  
> 适用于数据分析实习岗位简历展示

## 项目概述

本项目对巴西最大电商平台 Olist 的 **100,000+ 笔订单**进行全链路分析，涵盖销售趋势、用户行为、商品表现、物流与评价等多个维度，最终输出业务可落地的优化建议。

## 分析框架

```
数据清洗 → 探索性分析 → 多维下钻 → 洞察提炼 → 业务建议
```

| 模块 | 核心内容 | 关键技术 |
|------|---------|---------|
| 数据清洗 | 多表关联、缺失值处理、异常值检测 | Pandas, NumPy |
| 销售趋势 | 时序分析、季节性、地理分布 | Matplotlib, Seaborn |
| 用户分析 | RFM 分层、复购率、留存分析 | Pandas, Cohort Analysis |
| 商品分析 | 品类表现、价格弹性、评分驱动 | 统计分析, 可视化 |
| 综合报告 | KPI Dashboard、业务建议 | 商业分析思维 |

## 数据集

- **来源**: [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)
- **规模**: 9 张表, 100k+ 订单, 2016-2018
- **表结构**:
  - `orders` — 订单主表（状态、时间戳）
  - `customers` — 客户（地理位置）
  - `order_items` — 订单明细（商品、价格、运费）
  - `products` — 商品（品类、描述、尺寸）
  - `sellers` — 卖家（地理位置）
  - `order_payments` — 支付（方式、分期）
  - `order_reviews` — 评价（评分、评论文本）
  - `product_category_name_translation` — 品类英文翻译
  - `geolocation` — 巴西邮编经纬度

## 项目结构

```
olist-ecommerce-analysis/
├── README.md
├── data/                              # 原始数据（需从 Kaggle 下载）
├── notebooks/
│   ├── 01_data_cleaning_eda.ipynb     # 数据清洗与探索性分析
│   ├── 02_sales_trends.ipynb          # 销售趋势与业务分析
│   ├── 03_customer_product.ipynb      # 用户行为与商品分析
│   └── 04_executive_report.ipynb      # 综合分析报告
└── images/                            # 保存的关键图表
```

## 环境要求

```bash
pip install pandas numpy matplotlib seaborn jupyter
```

## 快速开始

1. 从 [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) 下载数据集，解压到 `data/` 目录
2. 运行 Jupyter: `jupyter notebook`
3. 按编号顺序打开 notebooks 进行分析

## 核心发现（示例）

- 📈 **销售高峰**：黑色星期五、圣诞节前后订单量激增 200%+
- 👥 **用户分层**：Top 20% 客户贡献 60%+ GMV（帕累托分布）
- ⭐ **评分驱动**：物流时效是评分的最强影响因子（相关性 0.42）
- 💳 **支付偏好**：信用卡占 75%，分期用户客单价高出 40%

## 作者

- 项目目的：数据分析实习岗位申请
- 技能展示：Python · Pandas · 数据可视化 · 业务分析 · SQL 思维
