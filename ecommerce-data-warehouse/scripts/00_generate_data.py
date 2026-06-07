"""
ShopEasy 电商数据仓库 - Step 0: 生成模拟业务数据

生成三张业务源表：
  1. users.csv      — 用户信息表（5,000 行）
  2. products.csv   — 商品信息表（500 行）
  3. orders.csv     — 订单事实表（25,000 行）

设计原则：
  - 使用固定随机种子（seed=42），确保数据可复现
  - 模拟真实电商数据分布：帕累托品类分布、周周期效应、城市层级差异
  - 引入适度数据质量问题（少量空值、异常值），用于后续质量检查演示
"""

import numpy as np
import pandas as pd
from pathlib import Path
import sys

# 添加 scripts 目录到 path，以便导入 utils
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_config, ensure_dir, logger

# ============================================================
# 配置与常量
# ============================================================
config = load_config()
RNG = np.random.default_rng(config["generate"]["seed"])

# 中国城市列表（模拟不同层级城市）
CITIES_TIER1 = ["北京", "上海", "广州", "深圳"]
CITIES_TIER2 = ["杭州", "成都", "武汉", "南京", "重庆", "西安", "长沙", "苏州", "天津", "郑州"]
CITIES_TIER3 = ["合肥", "福州", "厦门", "昆明", "南宁", "贵阳", "南昌", "太原", "石家庄", "哈尔滨",
                "长春", "沈阳", "济南", "青岛", "大连", "无锡", "宁波", "佛山", "东莞", "温州"]
ALL_CITIES = CITIES_TIER1 + CITIES_TIER2 + CITIES_TIER3

# 商品分类体系（两级）
CATEGORIES = {
    "服装鞋帽": ["女装", "男装", "童装", "鞋靴", "运动户外"],
    "数码家电": ["手机", "电脑", "影音娱乐", "生活电器", "智能设备"],
    "食品生鲜": ["休闲零食", "生鲜水果", "粮油调味", "乳饮酒水", "营养保健"],
    "家居日用": ["家纺", "厨具", "收纳清洁", "家装建材", "家具"],
    "美妆个护": ["面部护肤", "彩妆", "身体护理", "口腔护理", "香水香氛"],
    "母婴玩具": ["奶粉辅食", "纸尿裤", "益智玩具", "童车童床", "孕产用品"],
}

# 品牌池
BRANDS_PREMIUM = ["Apple", "华为", "戴森", "雅诗兰黛", "耐克", "阿迪达斯", "海尔", "格力", "飞利浦", "美的"]
BRANDS_STANDARD = ["小米", "vivo", "OPPO", "苏泊尔", "九阳", "欧莱雅", "自然堂", "安踏", "李宁", "良品铺子",
                   "三只松鼠", "百草味", "蓝月亮", "立白", "维达", "洁柔", "晨光", "得力", "乐高", "花王"]
BRANDS_BUDGET = ["南极人", "北极绒", "倍思", "品胜", "一加", "realme", "蜂花", "大宝", "回力", "鸿星尔克",
                 "得力", "齐心", "博世", "张小泉", "天堂", "恒源祥"]
ALL_BRANDS = BRANDS_PREMIUM + BRANDS_STANDARD + BRANDS_BUDGET

# 会员等级分布（模拟电商金字塔）
MEMBERSHIP_WEIGHTS = {
    "普通会员": 0.50,
    "银卡会员": 0.25,
    "金卡会员": 0.15,
    "钻石会员": 0.07,
    "黑金会员": 0.03,
}

# 订单状态分布（大部分已完成）
ORDER_STATUS_WEIGHTS = {
    "已完成": 0.70,
    "已发货": 0.12,
    "待发货": 0.08,
    "已取消": 0.07,
    "已退款": 0.03,
}

# 注册渠道
CHANNELS = ["APP", "小程序", "H5网页", "PC网页", "线下推广"]
CHANNEL_WEIGHTS = [0.40, 0.30, 0.12, 0.10, 0.08]

# 年龄段
AGE_GROUPS = ["18-24岁", "25-34岁", "35-44岁", "45-54岁", "55岁以上"]
AGE_WEIGHTS = [0.20, 0.40, 0.25, 0.10, 0.05]

# 供应商
SUPPLIERS = [f"供应商_{chr(65+i)}" for i in range(20)]


def generate_users(n_users: int) -> pd.DataFrame:
    """
    生成用户信息表。

    设计要点：
      - 注册时间两年前开始分布，新用户随时间递增（模拟增长）
      - 一线城市用户占 35%，二线 40%，三线 25%
      - 高等级会员的注册时间更早（有升级过程）
    """
    logger.info(f"生成用户表: {n_users:,} 行...")

    # 用户 ID
    user_ids = [f"U{str(i).zfill(6)}" for i in range(1, n_users + 1)]

    # 注册时间：2022-01-01 到 2025-12-31，新用户概率递增
    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2025-12-31")
    days_range = (end - start).days

    # 使用 Beta 分布使新用户占比更高（模拟增长）
    raw_days = RNG.beta(2, 1, size=n_users) * days_range
    register_dates = pd.to_datetime(
        [start + pd.Timedelta(days=int(d)) for d in raw_days]
    ).sort_values()

    # 城市分配：一线多、三线少
    city_weights_tiers = (
        [0.08] * len(CITIES_TIER1) +   # 一线 4 城共 32%
        [0.04] * len(CITIES_TIER2) +   # 二线 10 城共 40%
        [0.014] * len(CITIES_TIER3)    # 三线 20 城共 28%
    )
    # 归一化
    total_w = sum(city_weights_tiers)
    city_weights = [w / total_w for w in city_weights_tiers]

    cities = RNG.choice(ALL_CITIES, size=n_users, p=city_weights)

    # 会员等级：与注册时间相关（注册越早，等级越高）
    membership_levels = RNG.choice(
        list(MEMBERSHIP_WEIGHTS.keys()),
        size=n_users,
        p=list(MEMBERSHIP_WEIGHTS.values()),
    )
    # 后处理：较早注册的用户中随机提升一些为高等级
    ranks = {"普通会员": 0, "银卡会员": 1, "金卡会员": 2, "钻石会员": 3, "黑金会员": 4}
    for i in range(n_users):
        # 注册时间越早，有一定概率升级
        days_since_register = (end - register_dates[i]).days
        if days_since_register > 900 and RNG.random() < 0.3:  # 2.5年+的用户30%概率提升一级
            current_rank = ranks[membership_levels[i]]
            if current_rank < 4:
                # 找到下一级
                for level, rank in ranks.items():
                    if rank == current_rank + 1:
                        membership_levels[i] = level
                        break

    # 渠道
    channels = RNG.choice(CHANNELS, size=n_users, p=CHANNEL_WEIGHTS)

    # 性别（引入少量缺失值作为数据质量问题）
    genders = RNG.choice(["男", "女"], size=n_users, p=[0.48, 0.52])
    # 随机 2% 设为空（模拟数据质量问题）
    null_mask_gender = RNG.random(n_users) < 0.02
    genders[null_mask_gender] = None

    # 年龄段
    age_groups = RNG.choice(AGE_GROUPS, size=n_users, p=AGE_WEIGHTS)
    null_mask_age = RNG.random(n_users) < 0.01
    age_groups[null_mask_age] = None

    df = pd.DataFrame({
        "user_id": user_ids,
        "register_time": register_dates.strftime("%Y-%m-%d"),
        "city": cities,
        "membership_level": membership_levels,
        "channel": channels,
        "gender": genders,
        "age_group": age_groups,
    })

    logger.info(f"  用户表生成完成: {len(df):,} 行, {len(df.columns)} 列")
    return df


def generate_products(n_products: int) -> pd.DataFrame:
    """
    生成商品信息表。

    设计要点：
      - 品类帕累托分布（20% 品类贡献 80% 商品数）
      - 价格服从对数正态分布，不同品类有不同的价格区间
      - 成本价 = 售价 * (0.3~0.7)
    """
    logger.info(f"生成商品表: {n_products:,} 行...")

    # 展开所有二级品类
    all_subcategories = []
    for l1, l2_list in CATEGORIES.items():
        for l2 in l2_list:
            all_subcategories.append((l1, l2))

    # 帕累托分布：前 20% 品类拥有更多商品
    n_cats = len(all_subcategories)
    cat_indices = RNG.pareto(2.0, size=n_products).astype(int) % n_cats

    product_ids = [f"P{str(i).zfill(5)}" for i in range(1, n_products + 1)]

    # 按品类生成价格
    cat_price_ranges = {}
    for l1, l2 in all_subcategories:
        if l1 == "服装鞋帽":
            base = RNG.choice([80, 150, 250, 400, 600])
        elif l1 == "数码家电":
            base = RNG.choice([500, 1500, 3000, 6000, 10000])
        elif l1 == "食品生鲜":
            base = RNG.choice([15, 35, 60, 100, 200])
        elif l1 == "家居日用":
            base = RNG.choice([30, 80, 200, 500, 1500])
        elif l1 == "美妆个护":
            base = RNG.choice([40, 100, 250, 500, 1200])
        else:  # 母婴玩具
            base = RNG.choice([50, 120, 300, 800, 2000])
        cat_price_ranges[(l1, l2)] = base

    categories_l1 = []
    categories_l2 = []
    unit_prices = []
    cost_prices = []
    brands = []
    suppliers = []

    for i in range(n_products):
        l1, l2 = all_subcategories[cat_indices[i]]
        categories_l1.append(l1)
        categories_l2.append(l2)

        base = cat_price_ranges[(l1, l2)]
        # 对数正态分布，mu = log(base), sigma = 0.5
        price = RNG.lognormal(mean=np.log(base), sigma=0.5)
        price = round(max(5, min(50000, price)), 2)  # 裁剪到合理范围
        unit_prices.append(price)

        # 成本率：30%~70%
        cost_rate = RNG.uniform(0.30, 0.70)
        cost_prices.append(round(price * cost_rate, 2))

        # 品牌：根据品类选择
        if l1 in ["数码家电"]:
            brand_pool = BRANDS_PREMIUM + BRANDS_STANDARD
        elif l1 in ["美妆个护"]:
            brand_pool = BRANDS_PREMIUM + BRANDS_STANDARD
        else:
            brand_pool = ALL_BRANDS
        brands.append(RNG.choice(brand_pool))

        suppliers.append(RNG.choice(SUPPLIERS))

    # 引入少量缺失品牌（2%）
    for i in range(n_products):
        if RNG.random() < 0.02:
            brands[i] = None

    df = pd.DataFrame({
        "product_id": product_ids,
        "category_l1": categories_l1,
        "category_l2": categories_l2,
        "brand": brands,
        "unit_price": unit_prices,
        "cost_price": cost_prices,
        "supplier": suppliers,
    })

    logger.info(f"  商品表生成完成: {len(df):,} 行, {len(df.columns)} 列")
    return df


def generate_orders(
    n_orders: int,
    users_df: pd.DataFrame,
    products_df: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    生成订单事实表。

    设计要点：
      - 周周期效应：周末订单量高 30%
      - 大促效应：6月、11月订单量显著上升（模拟618/双11）
      - 折扣与会员等级相关：高等级会员享受更高折扣
      - 不同城市订单金额差异（一线 > 二线 > 三线）
      - 部分订单状态与时间相关（早期订单偏向已完成）
    """
    logger.info(f"生成订单表: {n_orders:,} 行...")

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(date_range)

    # 每天的基础订单权重（周周期 + 大促效应）
    daily_weights = np.ones(n_days)
    for i, d in enumerate(date_range):
        # 周末权重 +30%
        if d.dayofweek >= 5:
            daily_weights[i] *= 1.30
        # 6月大促（618）+ 11月大促（双11）
        if d.month == 6:
            daily_weights[i] *= 1.50
        if d.month == 11:
            daily_weights[i] *= 2.00
        # 12月年末消费季
        if d.month == 12:
            daily_weights[i] *= 1.20

    daily_weights /= daily_weights.sum()

    # 为每个订单分配日期
    day_indices = RNG.choice(n_days, size=n_orders, p=daily_weights)
    order_dates = date_range[day_indices]

    # 订单 ID
    order_ids = [f"ORD{str(i).zfill(8)}" for i in range(1, n_orders + 1)]

    # 随机分配用户和商品
    user_indices = RNG.integers(0, len(users_df), size=n_orders)
    product_indices = RNG.integers(0, len(products_df), size=n_orders)

    user_ids = users_df["user_id"].iloc[user_indices].values
    product_ids = products_df["product_id"].iloc[product_indices].values
    unit_prices = products_df["unit_price"].iloc[product_indices].values
    user_memberships = users_df["membership_level"].iloc[user_indices].values
    user_cities = users_df["city"].iloc[user_indices].values

    # 折扣率：根据会员等级
    discount_rates = np.zeros(n_orders)
    membership_discount = {
        "普通会员": (0.0, 0.10),
        "银卡会员": (0.02, 0.15),
        "金卡会员": (0.05, 0.20),
        "钻石会员": (0.08, 0.30),
        "黑金会员": (0.10, 0.35),
    }

    for i in range(n_orders):
        lo, hi = membership_discount.get(user_memberships[i], (0.0, 0.10))
        # 大促期间折扣更高
        month = order_dates[i].month
        if month in [6, 11]:
            lo += 0.05
            hi += 0.10
        discount_rates[i] = round(RNG.uniform(lo, min(hi, 0.50)), 2)

    # 购买数量（大部分为1，偶尔多件）
    quantities = RNG.choice([1, 1, 1, 1, 1, 2, 2, 3, 4, 5], size=n_orders)

    # 计算金额
    order_amounts = np.round(unit_prices * quantities, 2)
    discounts = np.round(order_amounts * discount_rates, 2)
    actual_amounts = np.round(order_amounts - discounts, 2)
    # 确保实际金额不为负
    actual_amounts = np.maximum(actual_amounts, 1.0)

    # 订单状态：早期订单更偏向已完成
    order_statuses = []
    for i, d in enumerate(order_dates):
        days_ago = (date_range[-1] - d).days
        if days_ago > 30:
            # 30天前的订单：大部分已完成
            status_weights = {"已完成": 0.85, "已退款": 0.05, "已取消": 0.10}
        elif days_ago > 7:
            status_weights = {"已完成": 0.55, "已发货": 0.20, "待发货": 0.10, "已取消": 0.10, "已退款": 0.05}
        else:
            status_weights = {"待发货": 0.25, "已发货": 0.30, "已完成": 0.25, "已取消": 0.15, "已退款": 0.05}

        statuses = list(status_weights.keys())
        probs = list(status_weights.values())
        # 归一化
        probs = [p / sum(probs) for p in probs]
        order_statuses.append(RNG.choice(statuses, p=probs))

    # 支付时间和订单时间的间隔
    payment_hours = RNG.exponential(2, size=n_orders).astype(int)
    payment_times = [
        (order_dates[i] + pd.Timedelta(hours=int(min(h, 72))))
        if order_statuses[i] not in ["已取消"]
        else None
        for i, h in enumerate(payment_hours)
    ]

    # 收货城市（大部分与用户注册城市相同，少部分不同）
    shipping_cities = []
    for i, city in enumerate(user_cities):
        if RNG.random() < 0.85:
            shipping_cities.append(city)
        else:
            shipping_cities.append(RNG.choice(ALL_CITIES))

    df = pd.DataFrame({
        "order_id": order_ids,
        "user_id": user_ids,
        "product_id": product_ids,
        "quantity": quantities,
        "unit_price": unit_prices,
        "order_amount": order_amounts,
        "discount": discounts,
        "discount_rate": discount_rates,
        "actual_amount": actual_amounts,
        "order_status": order_statuses,
        "order_time": order_dates.strftime("%Y-%m-%d %H:%M:%S"),
        "payment_time": [
            t.strftime("%Y-%m-%d %H:%M:%S") if t is not None else None
            for t in payment_times
        ],
        "shipping_city": shipping_cities,
    })

    # 引入少量缺失支付时间（5% 未支付/已取消场景外额外加一些）
    for i in range(n_orders):
        if df["order_status"].iloc[i] == "已取消":
            df.iloc[i, df.columns.get_loc("payment_time")] = None

    logger.info(f"  订单表生成完成: {len(df):,} 行, {len(df.columns)} 列")
    return df


def save_data(df: pd.DataFrame, filename: str, config: dict) -> None:
    """保存 DataFrame 到 raw 目录。"""
    raw_dir = Path(__file__).resolve().parent.parent / config["data"]["raw_dir"]
    ensure_dir(raw_dir)
    filepath = raw_dir / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    logger.info(f"  已保存: {filepath} ({len(df):,} 行)")


def main():
    """主流程：依次生成三张源表并保存。"""
    print()
    logger.info("=" * 60)
    logger.info("  ShopEasy 电商数据仓库 - 模拟数据生成")
    logger.info("=" * 60)
    logger.info(f"  随机种子: {config['generate']['seed']}")
    logger.info(f"  日期范围: {config['generate']['start_date']} ~ {config['generate']['end_date']}")
    logger.info("")

    # 1. 生成用户表
    users_df = generate_users(config["generate"]["n_users"])
    save_data(users_df, "users.csv", config)

    # 2. 生成商品表
    products_df = generate_products(config["generate"]["n_products"])
    save_data(products_df, "products.csv", config)

    # 3. 生成订单表（依赖用户和商品）
    orders_df = generate_orders(
        config["generate"]["n_orders"],
        users_df,
        products_df,
        config["generate"]["start_date"],
        config["generate"]["end_date"],
    )
    save_data(orders_df, "orders.csv", config)

    # 汇总统计
    logger.info("")
    logger.info("=" * 60)
    logger.info("  数据生成完成！汇总：")
    logger.info(f"    用户表:   {len(users_df):,} 行 × {len(users_df.columns)} 列")
    logger.info(f"    商品表:   {len(products_df):,} 行 × {len(products_df.columns)} 列")
    logger.info(f"    订单表:   {len(orders_df):,} 行 × {len(orders_df.columns)} 列")
    logger.info(f"    日期范围: {orders_df['order_time'].min()} ~ {orders_df['order_time'].max()}")
    logger.info(f"    总交易额: ¥{orders_df['actual_amount'].sum():,.2f}")
    logger.info("=" * 60)
    print()


if __name__ == "__main__":
    main()
