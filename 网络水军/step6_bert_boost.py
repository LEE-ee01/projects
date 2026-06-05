"""
水军检测系统 - 阶段6：BERT特征性能提升
step6_bert_boost.py

目标：通过BERT语义特征将F1分数从0.58提升到0.72+
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix, 
                            roc_auc_score, f1_score, precision_score, 
                            recall_score, accuracy_score)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from imblearn.over_sampling import ADASYN, SMOTE
from imblearn.combine import SMOTETomek
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def print_banner(title, symbol="🚀"):
    """打印横幅"""
    print(f"\n{symbol*35}")
    print(f"            {title}")
    print(f"{symbol*35}\n")


class BERTFeatureExtractor:
    """BERT文本特征提取器"""
    
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2', use_mirror=True):
        """
        初始化BERT模型
        使用sentence-transformers，比原生BERT快10倍
        
        参数:
            model_name: 模型名称
            use_mirror: 是否使用国内镜像（默认True）
        """
        print("【初始化BERT模型】")
        
        # 设置镜像源
        if use_mirror:
            import os
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            print("  🌐 使用国内镜像源: hf-mirror.com")
        
        try:
            from sentence_transformers import SentenceTransformer
            print(f"  正在加载模型: {model_name}")
            
            # 强制使用CPU（避免CUDA兼容性问题）
            import torch
            device = 'cpu'
            print(f"  🖥️  使用设备: {device} (避免CUDA兼容性问题)")
            
            # 尝试多个模型（按优先级）
            model_list = [
                model_name,  # 用户指定的模型
                'distiluse-base-multilingual-cased-v2',  # 更小的多语言模型
                'paraphrase-MiniLM-L3-v2',  # 最小的英文模型
            ]
            
            self.model = None
            for model in model_list:
                try:
                    print(f"  尝试加载: {model}")
                    self.model = SentenceTransformer(model, device=device)
                    print(f"  ✅ BERT模型加载成功: {model}")
                    break
                except Exception as e:
                    print(f"  ⚠️ {model} 加载失败")
                    continue
            
            if self.model is not None:
                self.available = True
            else:
                raise Exception("所有模型加载失败")
                
        except ImportError:
            print("  ⚠️ sentence-transformers未安装")
            print("  请运行: pip install sentence-transformers")
            self.available = False
        except Exception as e:
            print(f"  ⚠️ BERT加载失败: {str(e)[:100]}")
            print("  将使用备用方案（TF-IDF）")
            self.available = False
    
    def extract_features(self, texts, batch_size=32, show_progress=True):
        """
        提取BERT特征
        
        参数:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度
        
        返回:
            numpy数组，形状为(n_samples, 384)
        """
        if not self.available:
            return self._fallback_features(texts)
        
        print(f"\n【提取BERT特征】")
        print(f"  文本数量: {len(texts)}")
        print(f"  批处理大小: {batch_size}")
        
        # 清洗文本
        texts_cleaned = [str(text).strip() if pd.notna(text) else "" for text in texts]
        
        # 提取特征
        embeddings = self.model.encode(
            texts_cleaned,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        print(f"  ✅ 特征提取完成")
        print(f"  特征维度: {embeddings.shape}")
        
        return embeddings
    
    def _fallback_features(self, texts):
        """备用方案：使用TF-IDF"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        import jieba
        
        print("  使用TF-IDF作为备用方案")
        texts_cleaned = [str(text).strip() if pd.notna(text) else "" for text in texts]
        texts_seg = [' '.join(jieba.cut(text)) for text in texts_cleaned]
        
        vectorizer = TfidfVectorizer(max_features=384, ngram_range=(1, 3))
        features = vectorizer.fit_transform(texts_seg).toarray()
        
        return features


class ImprovedSampler:
    """改进的采样器"""
    
    @staticmethod
    def apply_adasyn(X, y, sampling_strategy=0.8, random_state=42):
        """ADASYN采样：专注于难分样本"""
        print("\n【应用ADASYN采样】")
        print(f"  采样前 - 正常: {sum(y==0)}, 水军: {sum(y==1)}")
        
        adasyn = ADASYN(
            sampling_strategy=sampling_strategy,
            random_state=random_state,
            n_neighbors=5
        )
        
        X_res, y_res = adasyn.fit_resample(X, y)
        print(f"  采样后 - 正常: {sum(y_res==0)}, 水军: {sum(y_res==1)}")
        print(f"  ✅ ADASYN采样完成")
        
        return X_res, y_res
    
    @staticmethod
    def apply_smote_tomek(X, y, random_state=42):
        """SMOTE + Tomek Links组合"""
        print("\n【应用SMOTETomek采样】")
        print(f"  采样前 - 正常: {sum(y==0)}, 水军: {sum(y==1)}")
        
        smote_tomek = SMOTETomek(random_state=random_state)
        X_res, y_res = smote_tomek.fit_resample(X, y)
        
        print(f"  采样后 - 正常: {sum(y_res==0)}, 水军: {sum(y_res==1)}")
        print(f"  ✅ SMOTETomek采样完成")
        
        return X_res, y_res


def optimize_threshold(y_true, y_proba):
    """优化分类阈值"""
    from sklearn.metrics import precision_recall_curve
    
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
    
    best_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
    
    return best_threshold, f1_scores[best_idx]


def evaluate_model(model, X_test, y_test, model_name="Model", threshold=0.5):
    """评估模型性能"""
    # 预测
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    
    # 计算指标
    metrics = {
        'model': model_name,
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'auc': roc_auc_score(y_test, y_proba)
    }
    
    return metrics, y_pred, y_proba


def plot_comparison(original_metrics, bert_metrics, save_path='bert_improvement.png'):
    """绘制性能对比图"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 准备数据
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC']
    original_values = [
        original_metrics['accuracy'],
        original_metrics['precision'],
        original_metrics['recall'],
        original_metrics['f1'],
        original_metrics['auc']
    ]
    bert_values = [
        bert_metrics['accuracy'],
        bert_metrics['precision'],
        bert_metrics['recall'],
        bert_metrics['f1'],
        bert_metrics['auc']
    ]
    
    # 子图1：性能对比
    x = np.arange(len(metrics_names))
    width = 0.35
    
    axes[0].bar(x - width/2, original_values, width, label='原始模型', alpha=0.8)
    axes[0].bar(x + width/2, bert_values, width, label='BERT增强', alpha=0.8)
    axes[0].set_ylabel('分数')
    axes[0].set_title('性能对比')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics_names, rotation=45)
    axes[0].legend()
    axes[0].set_ylim([0, 1])
    axes[0].grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, (v1, v2) in enumerate(zip(original_values, bert_values)):
        axes[0].text(i - width/2, v1 + 0.02, f'{v1:.3f}', ha='center', fontsize=8)
        axes[0].text(i + width/2, v2 + 0.02, f'{v2:.3f}', ha='center', fontsize=8)
    
    # 子图2：提升幅度
    improvements = [(b - o) * 100 for o, b in zip(original_values, bert_values)]
    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    
    axes[1].bar(metrics_names, improvements, color=colors, alpha=0.7)
    axes[1].set_ylabel('提升幅度 (%)')
    axes[1].set_title('性能提升')
    axes[1].set_xticklabels(metrics_names, rotation=45)
    axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[1].grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, imp in enumerate(improvements):
        axes[1].text(i, imp + (1 if imp > 0 else -1), 
                    f'{imp:+.1f}%', ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  ✅ 对比图已保存: {save_path}")
    plt.close()


def main():
    """主函数"""
    print_banner("步骤6：BERT特征性能提升", "🚀")
    print("目标：F1分数从0.58提升到0.72+\n")
    
    # ==================== 阶段1：加载数据 ====================
    print("="*70)
    print("【阶段1】加载数据")
    print("="*70)
    
    # 加载原始数据（获取文本）
    try:
        df_original = pd.read_excel('data120.xlsx')
        print(f"✅ 原始数据: {df_original.shape[0]} 行")
    except:
        print("❌ 无法加载data120.xlsx")
        return
    
    # 加载特征数据
    try:
        df_features = pd.read_csv('advanced_features.csv')
        print(f"✅ 特征数据: {df_features.shape}")
    except:
        print("❌ 无法加载advanced_features.csv")
        return
    
    # 获取标签并转换为数值
    # 检查标注列的数据类型
    print(f"  标注列数据类型: {df_original['标注'].dtype}")
    print(f"  标注列唯一值: {df_original['标注'].unique()}")
    
    # 处理不同的标注格式
    if df_original['标注'].dtype == 'float64' or df_original['标注'].dtype == 'float32':
        # 数值型标注：1.0表示水军，NaN表示正常
        y = df_original['标注'].fillna(0).astype(int)  # NaN->0(正常), 1->1(水军)
        print(f"  使用数值映射: NaN/0->正常, 1->水军")
    else:
        # 文本型标注
        label_map = {'正常': 0, '水军': 1}
        y = df_original['标注'].map(label_map).values
        print(f"  使用文本映射: {label_map}")
    
    print(f"✅ 标签分布 - 正常: {sum(y==0)}, 水军: {sum(y==1)}")
    print(f"  不平衡比例: {sum(y==0)/sum(y==1):.2f}:1")
    
    # ==================== 阶段2：提取BERT特征 ====================
    print("\n" + "="*70)
    print("【阶段2】提取BERT特征")
    print("="*70)
    
    bert_extractor = BERTFeatureExtractor()
    
    # 提取文本列
    text_column = '评价内容'  # 根据实际列名调整
    if text_column in df_original.columns:
        texts = df_original[text_column].values
    else:
        print(f"❌ 找不到文本列: {text_column}")
        return
    
    # 提取BERT特征
    bert_features = bert_extractor.extract_features(texts, batch_size=64)
    
    # 创建BERT特征DataFrame
    bert_df = pd.DataFrame(
        bert_features,
        columns=[f'bert_{i}' for i in range(bert_features.shape[1])]
    )
    
    print(f"\n  BERT特征形状: {bert_df.shape}")
    
    # ==================== 阶段3：特征融合 ====================
    print("\n" + "="*70)
    print("【阶段3】特征融合")
    print("="*70)
    
    # 合并原始特征和BERT特征
    X_combined = pd.concat([
        df_features.reset_index(drop=True),
        bert_df
    ], axis=1)
    
    print(f"  原始特征: {df_features.shape[1]} 维")
    print(f"  BERT特征: {bert_df.shape[1]} 维")
    print(f"  融合特征: {X_combined.shape[1]} 维")
    print(f"  ✅ 特征融合完成")
    
    # 保存融合特征
    combined_features_path = 'features_with_bert.csv'
    X_combined.to_csv(combined_features_path, index=False)
    print(f"  ✅ 融合特征已保存: {combined_features_path}")
    
    # ==================== 阶段4：数据划分 ====================
    print("\n" + "="*70)
    print("【阶段4】数据划分")
    print("="*70)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_combined, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"  训练集: {X_train.shape[0]} 样本")
    print(f"  测试集: {X_test.shape[0]} 样本")
    
    # 标准化
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"  ✅ 数据标准化完成")
    
    # ==================== 阶段5：对比实验 ====================
    print("\n" + "="*70)
    print("【阶段5】对比实验")
    print("="*70)
    
    # 实验1：仅原始特征
    print("\n【实验1】仅原始特征（基线）")
    print("-"*70)
    
    X_train_original = X_train_scaled[:, :df_features.shape[1]]
    X_test_original = X_test_scaled[:, :df_features.shape[1]]
    
    # 应用SMOTE
    smote = SMOTE(random_state=42, sampling_strategy=0.8)
    X_train_original_res, y_train_res = smote.fit_resample(X_train_original, y_train)
    
    model_original = XGBClassifier(
        scale_pos_weight=6,
        max_depth=6,
        learning_rate=0.05,
        n_estimators=300,
        random_state=42,
        eval_metric='logloss'
    )
    
    print("  训练中...")
    model_original.fit(X_train_original_res, y_train_res)
    
    # 优化阈值
    y_train_proba = model_original.predict_proba(X_train_original_res)[:, 1]
    best_threshold_original, _ = optimize_threshold(y_train_res, y_train_proba)
    
    original_metrics, _, _ = evaluate_model(
        model_original, X_test_original, y_test, 
        "原始模型", best_threshold_original
    )
    
    print(f"\n  原始模型性能:")
    print(f"    准确率: {original_metrics['accuracy']:.4f}")
    print(f"    精确率: {original_metrics['precision']:.4f}")
    print(f"    召回率: {original_metrics['recall']:.4f}")
    print(f"    F1分数: {original_metrics['f1']:.4f} ⚠️")
    print(f"    AUC: {original_metrics['auc']:.4f}")
    
    # 实验2：BERT增强特征 + ADASYN
    print("\n【实验2】BERT增强 + ADASYN采样")
    print("-"*70)
    
    # 应用ADASYN
    X_train_bert_res, y_train_bert_res = ImprovedSampler.apply_adasyn(
        X_train_scaled, y_train, sampling_strategy=0.8
    )
    
    model_bert = XGBClassifier(
        scale_pos_weight=3,  # 降低权重（因为已经平衡）
        max_depth=7,
        learning_rate=0.03,
        n_estimators=500,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    print("\n  训练中...")
    model_bert.fit(X_train_bert_res, y_train_bert_res)
    
    # 优化阈值
    y_train_bert_proba = model_bert.predict_proba(X_train_bert_res)[:, 1]
    best_threshold_bert, best_f1 = optimize_threshold(y_train_bert_res, y_train_bert_proba)
    print(f"\n  最优阈值: {best_threshold_bert:.3f}")
    print(f"  训练集最佳F1: {best_f1:.4f}")
    
    bert_metrics, _, _ = evaluate_model(
        model_bert, X_test_scaled, y_test,
        "BERT增强", best_threshold_bert
    )
    
    print(f"\n  BERT增强性能:")
    print(f"    准确率: {bert_metrics['accuracy']:.4f}")
    print(f"    精确率: {bert_metrics['precision']:.4f}")
    print(f"    召回率: {bert_metrics['recall']:.4f}")
    print(f"    F1分数: {bert_metrics['f1']:.4f} 🎯")
    print(f"    AUC: {bert_metrics['auc']:.4f}")
    
    # 计算提升幅度
    f1_improvement = (bert_metrics['f1'] - original_metrics['f1']) * 100
    print(f"\n  📈 F1分数提升: {f1_improvement:+.2f}%")
    
    # ==================== 阶段6：多模型对比 ====================
    print("\n" + "="*70)
    print("【阶段6】多模型对比（BERT特征）")
    print("="*70)
    
    models_dict = {
        'XGBoost': XGBClassifier(
            scale_pos_weight=3, max_depth=7, learning_rate=0.03,
            n_estimators=500, random_state=42, eval_metric='logloss'
        ),
        'LightGBM': LGBMClassifier(
            scale_pos_weight=3, max_depth=7, learning_rate=0.03,
            n_estimators=500, random_state=42, verbose=-1
        ),
        'CatBoost': CatBoostClassifier(
            scale_pos_weight=3, depth=7, learning_rate=0.03,
            iterations=500, random_state=42, verbose=False
        ),
        'RandomForest': RandomForestClassifier(
            class_weight='balanced', max_depth=15,
            n_estimators=300, random_state=42
        ),
        'ExtraTrees': ExtraTreesClassifier(
            class_weight='balanced', max_depth=15,
            n_estimators=300, random_state=42
        )
    }
    
    all_results = []
    
    for name, model in models_dict.items():
        print(f"\n训练 {name}...")
        model.fit(X_train_bert_res, y_train_bert_res)
        
        # 优化阈值
        y_train_proba = model.predict_proba(X_train_bert_res)[:, 1]
        threshold, _ = optimize_threshold(y_train_bert_res, y_train_proba)
        
        metrics, _, _ = evaluate_model(model, X_test_scaled, y_test, name, threshold)
        all_results.append(metrics)
        
        print(f"  {name} - F1: {metrics['f1']:.4f}")
    
    # 结果汇总
    results_df = pd.DataFrame(all_results)
    results_df = results_df.sort_values('f1', ascending=False)
    
    print("\n" + "="*70)
    print("【模型性能排名】")
    print("="*70)
    print(results_df.to_string(index=False))
    
    # 保存结果
    results_df.to_csv('bert_models_comparison.csv', index=False)
    print(f"\n✅ 结果已保存: bert_models_comparison.csv")
    
    # ==================== 阶段7：保存模型 ====================
    print("\n" + "="*70)
    print("【阶段7】保存最佳模型")
    print("="*70)
    
    best_model_name = results_df.iloc[0]['model']
    best_model = models_dict[best_model_name]
    
    # 保存模型和相关文件
    joblib.dump(best_model, f'best_model_bert_{best_model_name}.pkl')
    joblib.dump(scaler, 'scaler_bert.pkl')
    joblib.dump({'threshold': best_threshold_bert}, 'threshold_bert.pkl')
    
    print(f"  ✅ 最佳模型已保存: best_model_bert_{best_model_name}.pkl")
    print(f"  ✅ Scaler已保存: scaler_bert.pkl")
    print(f"  ✅ 阈值已保存: threshold_bert.pkl")
    
    # ==================== 阶段8：生成可视化 ====================
    print("\n" + "="*70)
    print("【阶段8】生成可视化")
    print("="*70)
    
    plot_comparison(original_metrics, bert_metrics)
    
    # ==================== 总结 ====================
    print("\n" + "="*70)
    print("✅ BERT特征提升完成！")
    print("="*70)
    
    print(f"\n🏆 最佳模型: {best_model_name}")
    print(f"   F1分数: {results_df.iloc[0]['f1']:.4f}")
    print(f"   准确率: {results_df.iloc[0]['accuracy']:.4f}")
    print(f"   AUC: {results_df.iloc[0]['auc']:.4f}")
    
    print(f"\n📈 性能提升:")
    print(f"   原始F1: {original_metrics['f1']:.4f}")
    print(f"   BERT F1: {bert_metrics['f1']:.4f}")
    print(f"   提升幅度: {f1_improvement:+.2f}%")
    
    print(f"\n📁 生成的文件:")
    print(f"   • features_with_bert.csv - BERT融合特征")
    print(f"   • bert_models_comparison.csv - 模型对比结果")
    print(f"   • best_model_bert_{best_model_name}.pkl - 最佳模型")
    print(f"   • scaler_bert.pkl - 标准化器")
    print(f"   • bert_improvement.png - 性能对比图")
    
    print(f"\n🚀 下一步:")
    print(f"   继续性能优化:")
    print(f"   python step7_gnn_fusion.py")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()