"""
特征工程模块 - 完整优化版
专门适配你的数据结构：用户名称, 级别, 评价星级, 评价内容, 标注, 时间
"""

import pandas as pd
import jieba
import re
import numpy as np
from datetime import datetime
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 停用词列表
STOPWORDS = set([
    "的", "了", "是", "我", "就", "都", "在", "也", "有", "和", "不",
    "，", "。", " ", "！", "?", "：", "...", "、", "（", "）", """, """,
    "很", "一个", "这个", "一些", "什么", "可以", "我们", "他们", "它",
    "你", "他", "它", "着", "还是", "要", "会", "吧", "啊", "嗯", "呢", "没", "么",
    "这", "那", "都", "又", "让", "给", "去", "来", "说", "到", "看", "为"
])


class AdvancedFeatureEngineering:
    """高级特征工程类"""
    
    def __init__(self):
        print("初始化特征工程器...")
        
    def preprocess_text(self, text):
        """文本预处理"""
        if pd.isna(text) or text == "":
            return ""
        text = str(text).strip()
        return text
    
    def extract_text_statistics(self, text):
        """
        提取文本统计特征
        返回10个文本特征
        """
        if not text:
            return {
                'text_length': 0,
                'word_count': 0,
                'unique_word_count': 0,
                'exclamation_count': 0,
                'question_count': 0,
                'special_char_ratio': 0,
                'digit_ratio': 0,
                'avg_word_length': 0,
                'repeated_char_ratio': 0,
                'vocabulary_richness': 0
            }
        
        # 基础统计
        text_length = len(text)
        
        # 分词
        words = list(jieba.cut(text))
        words_filtered = [w for w in words if w.strip() and w not in STOPWORDS]
        word_count = len(words_filtered)
        unique_word_count = len(set(words_filtered))
        
        # 标点符号
        exclamation_count = text.count('！') + text.count('!')
        question_count = text.count('？') + text.count('?')
        
        # 特殊字符比例
        special_chars = re.findall(r'[^\w\s]', text)
        special_char_ratio = len(special_chars) / text_length if text_length > 0 else 0
        
        # 数字比例
        digits = re.findall(r'\d', text)
        digit_ratio = len(digits) / text_length if text_length > 0 else 0
        
        # 平均词长
        avg_word_length = sum(len(w) for w in words_filtered) / word_count if word_count > 0 else 0
        
        # 重复字符比例（如"哈哈哈"）
        repeated_chars = re.findall(r'(.)\1{2,}', text)
        repeated_char_ratio = len(repeated_chars) / text_length if text_length > 0 else 0
        
        # 词汇丰富度
        vocabulary_richness = unique_word_count / word_count if word_count > 0 else 0
        
        return {
            'text_length': text_length,
            'word_count': word_count,
            'unique_word_count': unique_word_count,
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'special_char_ratio': special_char_ratio,
            'digit_ratio': digit_ratio,
            'avg_word_length': avg_word_length,
            'repeated_char_ratio': repeated_char_ratio,
            'vocabulary_richness': vocabulary_richness
        }
    
    def extract_user_behavior_features(self, data):
        """
        提取用户行为特征
        返回4个用户行为特征
        """
        features_list = []
        
        # 用户评论频率
        comment_freq = data['用户名称'].value_counts().to_dict()
        
        # 用户平均评分
        avg_rating = data.groupby('用户名称')['评价星级'].mean().to_dict()
        
        # 用户评分标准差
        rating_std = data.groupby('用户名称')['评价星级'].std().fillna(0).to_dict()
        
        # 用户评论时间间隔
        data_temp = data.copy()
        data_temp['时间'] = pd.to_datetime(data_temp['时间'], errors='coerce')
        
        user_time_intervals = {}
        for user in data_temp['用户名称'].unique():
            user_data = data_temp[data_temp['用户名称'] == user].sort_values('时间')
            if len(user_data) > 1 and user_data['时间'].notna().sum() > 1:
                time_diffs = user_data['时间'].diff().dt.total_seconds().dropna()
                avg_interval = time_diffs.mean() if len(time_diffs) > 0 else 0
            else:
                avg_interval = 0
            user_time_intervals[user] = avg_interval
        
        # 为每条评论生成特征
        for _, row in data.iterrows():
            user = row['用户名称']
            features_list.append({
                'comment_frequency': comment_freq.get(user, 1),
                'average_rating': avg_rating.get(user, 5.0),
                'rating_std': rating_std.get(user, 0),
                'avg_time_interval': user_time_intervals.get(user, 0)
            })
        
        return pd.DataFrame(features_list)
    
    def extract_time_features(self, data):
        """
        提取时间特征
        返回4个时间特征
        """
        features_list = []
        
        data_temp = data.copy()
        data_temp['时间'] = pd.to_datetime(data_temp['时间'], errors='coerce')
        
        for _, row in data_temp.iterrows():
            if pd.notna(row['时间']):
                features_list.append({
                    'hour': row['时间'].hour,
                    'day_of_week': row['时间'].dayofweek,
                    'is_weekend': 1 if row['时间'].dayofweek >= 5 else 0,
                    'is_night': 1 if row['时间'].hour >= 22 or row['时间'].hour <= 6 else 0
                })
            else:
                features_list.append({
                    'hour': 12,
                    'day_of_week': 3,
                    'is_weekend': 0,
                    'is_night': 0
                })
        
        return pd.DataFrame(features_list)
    
    def extract_rating_features(self, data):
        """
        提取评分特征
        返回2个评分特征
        """
        rating_features = pd.DataFrame({
            'rating': data['评价星级'],
            'is_extreme': data['评价星级'].apply(lambda x: 1 if x in [1, 5] else 0)
        })
        
        return rating_features
    
    def extract_all_features(self, data):
        """
        提取所有特征
        总共：10 + 4 + 4 + 2 = 20 个特征
        """
        print("\n" + "="*70)
        print("开始提取特征...")
        print("="*70)
        
        # 1. 文本统计特征（10个）
        print("\n[1/4] 提取文本统计特征...")
        text_features = data['评价内容'].apply(
            lambda x: self.extract_text_statistics(self.preprocess_text(x))
        )
        text_features_df = pd.DataFrame(text_features.tolist())
        print(f"      ✓ 完成！提取了 {text_features_df.shape[1]} 个文本特征")
        
        # 2. 用户行为特征（4个）
        print("\n[2/4] 提取用户行为特征...")
        user_features_df = self.extract_user_behavior_features(data)
        print(f"      ✓ 完成！提取了 {user_features_df.shape[1]} 个用户行为特征")
        
        # 3. 时间特征（4个）
        print("\n[3/4] 提取时间特征...")
        time_features_df = self.extract_time_features(data)
        print(f"      ✓ 完成！提取了 {time_features_df.shape[1]} 个时间特征")
        
        # 4. 评分特征（2个）
        print("\n[4/4] 提取评分特征...")
        rating_features_df = self.extract_rating_features(data)
        print(f"      ✓ 完成！提取了 {rating_features_df.shape[1]} 个评分特征")
        
        # 合并所有特征
        all_features = pd.concat([
            text_features_df,
            user_features_df,
            time_features_df,
            rating_features_df
        ], axis=1)
        
        print("\n" + "="*70)
        print(f"✅ 特征提取完成！")
        print(f"   总特征数: {all_features.shape[1]}")
        print(f"   数据行数: {all_features.shape[0]}")
        print("="*70)
        
        return all_features


def main():
    """主函数"""
    print("\n" + "🚀"*35)
    print("\n" + " "*20 + "步骤1：特征工程")
    print(" "*15 + "提取高级特征用于水军检测")
    print("\n" + "🚀"*35)
    
    # 1. 读取数据
    print("\n【阶段1】读取数据文件")
    print("-"*70)
    
    try:
        data = pd.read_excel("data120.xlsx")
        print(f"✅ 成功读取数据")
        print(f"   - 文件: data120.xlsx")
        print(f"   - 总行数: {len(data):,}")
        print(f"   - 总列数: {len(data.columns)}")
        print(f"   - 列名: {', '.join(data.columns)}")
        
        # 检查必要的列
        required_cols = ['用户名称', '评价内容', '评价星级', '时间']
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            print(f"\n❌ 错误：缺少必要的列: {', '.join(missing)}")
            return
        
        # 检查水军标注
        if '标注' in data.columns:
            water_army_count = data['标注'].sum()
            print(f"   - 水军标注: {int(water_army_count):,} 条 ({water_army_count/len(data)*100:.2f}%)")
        
    except FileNotFoundError:
        print("❌ 错误：找不到 data120.xlsx")
        print("   请确保数据文件在当前目录下")
        return
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return
    
    # 2. 提取特征
    print("\n【阶段2】特征提取")
    print("-"*70)
    
    try:
        feature_engineer = AdvancedFeatureEngineering()
        features = feature_engineer.extract_all_features(data)
        
    except Exception as e:
        print(f"\n❌ 特征提取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 保存特征
    print("\n【阶段3】保存特征文件")
    print("-"*70)
    
    try:
        # 保存为CSV
        output_file = "advanced_features.csv"
        features.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ 特征已保存")
        print(f"   - 文件名: {output_file}")
        print(f"   - 数据规模: {features.shape[0]:,} 行 × {features.shape[1]} 列")
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return
    
    # 4. 显示结果摘要
    print("\n【阶段4】特征预览")
    print("-"*70)
    print("\n特征列表:")
    for i, col in enumerate(features.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\n数据预览（前3行）:")
    print(features.head(3).to_string())
    
    print("\n特征统计:")
    print(features.describe().to_string())
    
    # 5. 成功提示
    print("\n" + "="*70)
    print("✅ 特征工程完成！")
    print("="*70)
    
    print("\n📁 生成的文件:")
    print("   • advanced_features.csv")
    
    print("\n🎯 特征概览:")
    print("   • 文本特征: 10个（长度、词数、标点等）")
    print("   • 用户行为: 4个（频率、评分、时间间隔）")
    print("   • 时间特征: 4个（小时、星期、周末、夜间）")
    print("   • 评分特征: 2个（评分、极端评分）")
    
    print("\n🚀 下一步:")
    print("   运行无监督检测模块:")
    print("   python step2_unsupervised_detection.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()