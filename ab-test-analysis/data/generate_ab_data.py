"""
ShopEasy A/B 测试 - 模拟实验数据生成

业务场景：
  ShopEasy 产品团队进行了一项推荐算法 A/B 测试，测试期为 14 天。
  - Control (A): 现有"热门商品"推荐算法
  - Treatment (B): 新的"个性化"推荐算法

假设：
  - 主指标（转化率）：B 组高于 A 组（~12% vs ~10%）
  - 次指标（客单价）：B 组可能低于 A 组（个性化推荐倾向推荐性价比商品）
  - 不同会员等级和设备类型有差异化效果

生成约 20,000 条用户实验记录。
"""

import numpy as np
import pandas as pd
from pathlib import Path

# 固定随机种子
RNG = np.random.default_rng(42)

# 输出路径
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = OUTPUT_DIR / "ab_test_data.csv"


def generate_ab_data(n_users: int = 20000) -> pd.DataFrame:
    """
    生成 A/B 测试数据集。

    每个用户分配到一个实验组，记录其是否看到推荐、是否点击、是否购买、购买金额。
    """

    # 实验分组：随机均分
    groups = RNG.choice(["A", "B"], size=n_users, p=[0.5, 0.5])

    # 用户属性
    membership_levels = RNG.choice(
        ["普通会员", "银卡会员", "金卡会员", "钻石会员", "黑金会员"],
        size=n_users,
        p=[0.45, 0.25, 0.15, 0.10, 0.05],
    )
    device_types = RNG.choice(
        ["Mobile", "Desktop", "Tablet"],
        size=n_users,
        p=[0.60, 0.30, 0.10],
    )

    # 会话时长（模拟用户参与度），对数正态分布
    session_duration = RNG.lognormal(mean=np.log(120), sigma=0.6, size=n_users).astype(int)
    session_duration = np.clip(session_duration, 10, 1800)

    # ============================================================
    # 模拟实验效果
    # ============================================================
    n = n_users

    # --- 基础转化率 ---
    base_conversion = np.full(n, 0.10)  # 基线 10%

    # Treatment B: 转化率提升 2pp（12%）
    base_conversion[groups == "B"] += 0.02

    # 会员等级调整
    membership_boost = np.zeros(n)
    membership_boost[membership_levels == "银卡会员"] = 0.01
    membership_boost[membership_levels == "金卡会员"] = 0.02
    membership_boost[membership_levels == "钻石会员"] = 0.03
    membership_boost[membership_levels == "黑金会员"] = 0.04
    base_conversion += membership_boost

    # Treatment B 对高等级会员效果更强（交互效应）
    for i in range(3, 5):  # 钻石、黑金
        mask = (groups == "B") & (membership_levels == ["普通会员", "银卡会员", "金卡会员", "钻石会员", "黑金会员"][i])
        base_conversion[mask] += 0.01

    # 加噪声（个体差异）
    noise = RNG.normal(0, 0.02, size=n)
    base_conversion = np.clip(base_conversion + noise, 0.01, 0.50)

    # 是否购买（Bernoulli 采样）
    made_purchase = RNG.random(n) < base_conversion

    # --- 是否看到推荐 ---
    saw_recommendation = RNG.random(n) < 0.85  # 85% 用户看到推荐位

    # --- 是否点击 ---
    base_ctr = np.full(n, 0.30)  # 基线 CTR 30%
    base_ctr[groups == "B"] += 0.05  # B 组 +5pp
    base_ctr = np.clip(base_ctr, 0.05, 0.80)
    clicked = (RNG.random(n) < base_ctr) & saw_recommendation

    # --- 客单价 ---
    # 基础 AOV ~1200，对数正态
    base_aov = RNG.lognormal(mean=np.log(1200), sigma=0.5, size=n)
    # B 组客单价略低（个性化推荐倾向于性价比商品）
    base_aov[groups == "B"] *= 0.92
    # 会员调整
    aov_boost = np.ones(n)
    aov_boost[membership_levels == "银卡会员"] = 1.05
    aov_boost[membership_levels == "金卡会员"] = 1.15
    aov_boost[membership_levels == "钻石会员"] = 1.25
    aov_boost[membership_levels == "黑金会员"] = 1.40
    base_aov *= aov_boost
    base_aov = np.clip(base_aov, 10, 50000)

    # 未购买的用户客单价设为 0
    order_amount = np.where(made_purchase, np.round(base_aov, 2), 0.0)

    # ============================================================
    # 组装 DataFrame
    # ============================================================
    user_ids = [f"AB{str(i).zfill(6)}" for i in range(1, n_users + 1)]

    df = pd.DataFrame({
        "user_id": user_ids,
        "group": groups,
        "membership_level": membership_levels,
        "device_type": device_types,
        "session_duration": session_duration,
        "saw_recommendation": saw_recommendation,
        "clicked": clicked,
        "made_purchase": made_purchase,
        "order_amount": order_amount,
    })

    return df


def main():
    print("生成 A/B 测试模拟数据...")
    df = generate_ab_data(20000)

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"已保存: {OUTPUT_PATH} ({len(df):,} 行 × {len(df.columns)} 列)")

    # 快速统计
    print(f"\n数据摘要:")
    print(f"  A 组: {(df['group'] == 'A').sum():,} 用户")
    print(f"  B 组: {(df['group'] == 'B').sum():,} 用户")
    print(f"  A 组转化率: {df[df['group'] == 'A']['made_purchase'].mean():.2%}")
    print(f"  B 组转化率: {df[df['group'] == 'B']['made_purchase'].mean():.2%}")
    print(f"  A 组平均客单价: ¥{df[df['group'] == 'A']['order_amount'][df[df['group'] == 'A']['order_amount'] > 0].mean():.0f}")
    print(f"  B 组平均客单价: ¥{df[df['group'] == 'B']['order_amount'][df[df['group'] == 'B']['order_amount'] > 0].mean():.0f}")


if __name__ == "__main__":
    main()
