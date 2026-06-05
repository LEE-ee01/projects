"""
Olist 电商数据集下载脚本
支持多个数据源自动尝试下载
"""
import os
import sys
import zipfile
import requests
from io import BytesIO

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 预期的 9 个 CSV 文件
EXPECTED_FILES = [
    'olist_orders_dataset.csv',
    'olist_order_items_dataset.csv',
    'olist_order_payments_dataset.csv',
    'olist_order_reviews_dataset.csv',
    'olist_products_dataset.csv',
    'olist_customers_dataset.csv',
    'olist_sellers_dataset.csv',
    'olist_geolocation_dataset.csv',
    'product_category_name_translation.csv',
]


def check_existing():
    """检查数据是否已经下载"""
    existing = [f for f in EXPECTED_FILES if os.path.exists(os.path.join(DATA_DIR, f))]
    if len(existing) == len(EXPECTED_FILES):
        print(f"✅ 所有 {len(EXPECTED_FILES)} 个文件已存在于 data/ 目录")
        return True
    elif existing:
        print(f"⚠️  已找到 {len(existing)}/{len(EXPECTED_FILES)} 个文件，将尝试补全")
    return False


def download_via_kagglehub():
    """方法1: 使用 kagglehub (推荐)"""
    try:
        import kagglehub
        print("📥 正在通过 kagglehub 下载...")
        path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
        # 复制到 data/ 目录
        import shutil
        for f in os.listdir(path):
            src = os.path.join(path, f)
            dst = os.path.join(DATA_DIR, f)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
        print(f"✅ kagglehub 下载成功，文件保存至 {DATA_DIR}")
        return True
    except ImportError:
        print("⚠️  kagglehub 未安装，尝试其他方式...")
        return False
    except Exception as e:
        print(f"⚠️  kagglehub 下载失败: {e}")
        return False


def download_via_kaggle_api():
    """方法2: 使用 Kaggle API (需要设置 KAGGLE_USERNAME 和 KAGGLE_KEY)"""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("📥 正在通过 Kaggle API 下载...")
        api.dataset_download_files(
            "olistbr/brazilian-ecommerce",
            path=DATA_DIR,
            unzip=True
        )
        print(f"✅ Kaggle API 下载成功")
        return True
    except ImportError:
        print("⚠️  kaggle 包未安装，尝试其他方式...")
        return False
    except Exception as e:
        print(f"⚠️  Kaggle API 下载失败: {e}")
        return False


def verify():
    """验证下载完整性"""
    missing = [f for f in EXPECTED_FILES if not os.path.exists(os.path.join(DATA_DIR, f))]
    if not missing:
        print(f"\n✅ 验证通过！所有 {len(EXPECTED_FILES)} 个文件就绪")
        # 打印文件大小
        total_size = sum(
            os.path.getsize(os.path.join(DATA_DIR, f))
            for f in EXPECTED_FILES
        )
        print(f"📦 总大小: {total_size / 1024 / 1024:.1f} MB")
        return True
    else:
        print(f"\n❌ 缺少 {len(missing)} 个文件: {missing}")
        return False


def print_manual_instructions():
    """打印手动下载说明"""
    print("""
============================================================
📋 手动下载说明
============================================================

方法一（推荐 - 国内用户友好）：
  访问 和鲸社区: https://www.heywhale.com/mw/dataset/63ee1f10470e19e0b56d12ee
  点击下载按钮，解压到 data/ 目录

方法二：
  访问 Kaggle: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
  注册免费账号 → Download → 解压到 data/ 目录

方法三（Kaggle CLI）：
  pip install kaggle
  kaggle datasets download -d olistbr/brazilian-ecommerce
  unzip brazilian-ecommerce.zip -d data/

============================================================
""")


if __name__ == '__main__':
    print("=" * 60)
    print("📦 Olist 电商数据集下载工具")
    print("=" * 60)

    if check_existing():
        sys.exit(0)

    # 尝试自动下载
    success = download_via_kagglehub() or download_via_kaggle_api()

    if success:
        verify()
    else:
        print_manual_instructions()

    # 最终验证
    if not verify():
        print("\n💡 请按上述说明手动下载数据后重新运行此脚本验证")
        sys.exit(1)
