# ShopEasy 推荐算法 A/B 测试分析

## 项目概述

以 ShopEasy 电商平台推荐算法升级为背景，完成从实验设计、数据验证、统计检验到业务建议的**完整 A/B 测试分析流程**。

核心分析问题：**个性化推荐算法（Treatment B）是否优于热门推荐算法（Control A）？**

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.x |
| 数据处理 | Pandas, NumPy |
| 统计检验 | SciPy, Statsmodels |
| 可视化 | Matplotlib, Seaborn |
| 环境 | Jupyter Notebook |

## 实验设计

| 参数 | 值 |
|------|-----|
| 实验周期 | 14 天 |
| 样本量 | ~20,000 用户（A/B 各 ~10,000） |
| 主指标 | 转化率 (Conversion Rate) |
| 次指标 | 客单价 (AOV) |
| 护栏指标 | 推荐位点击率 (CTR) |
| 显著性水平 | α = 0.05 |

## 分析方法

1. **数据验证** — 卡方检验分流均匀性、功效分析样本量充足性
2. **主指标检验** — 双比例 Z 检验 + Bootstrap 置信区间
3. **次指标检验** — Welch's t 检验 + Cohen's d 效应量
4. **综合评估** — GMV Bootstrap CI
5. **分层分析** — 按会员等级、设备类型亚组分析 + Bonferroni 校正
6. **业务建议** — 基于统计证据的决策（全量 / 灰度 / 继续优化）

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成模拟数据
python data/generate_ab_data.py

# 3. 启动 Jupyter 并运行分析
jupyter notebook ab_test_analysis.ipynb
```

## 项目结构

```
ab-test-analysis/
├── README.md
├── requirements.txt
├── ab_test_analysis.ipynb      # 完整分析 Notebook
├── data/
│   ├── generate_ab_data.py     # 模拟数据生成脚本
│   └── ab_test_data.csv        # 生成的实验数据 (~20K 行)
└── output/
    └── figures/                # 分析图表输出
```

## 关键统计方法

| 步骤 | 方法 | 说明 |
|------|------|------|
| 分流验证 | χ² 检验 | 验证 A/B 组分配均匀 |
| 样本量 | Power Analysis | 确认统计功效 ≥ 0.80 |
| 转化率检验 | Two-Proportion Z-Test | 检验比例差异 |
| 置信区间 | Bootstrap (10,000 reps) | 稳健的效应量估计 |
| 客单价检验 | Welch's t-test | 不假设等方差 |
| 效应量 | Cohen's h / Cohen's d | 衡量差异的实际意义 |
| 分层分析 | Subgroup Z-Test | 不同用户群的差异化效果 |
| 多重比较 | Bonferroni Correction | 控制族系错误率 (FWER) |
