"""
水军检测系统 - 阶段7：图神经网络特征融合
step7_gnn_fusion.py

目标：将图网络特征融合到模型中，F1分数从0.84提升到0.86+
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
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import ADASYN
import networkx as nx
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


def print_banner(title, symbol="🕸️"):
    """打印横幅"""
    print(f"\n{symbol*35}")
    print(f"            {title}")
    print(f"{symbol*35}\n")


class GraphFeatureExtractor:
    """图特征提取器"""
    
    def __init__(self):
        """初始化图特征提取器"""
        self.graph = None
        print("【初始化图特征提取器】")
    
    def build_user_similarity_graph(self, df, text_column='评价内容', 
                                   user_column='用户名称', threshold=0.75):
        """
        构建用户相似度图
        
        参数:
            df: 数据框
            text_column: 文本列名
            user_column: 用户列名
            threshold: 相似度阈值
        
        返回:
            NetworkX图对象
        """
        print("\n【构建用户相似度图】")
        print(f"  相似度阈值: {threshold}")
        
        # 提取文本特征用于计算相似度
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import jieba
        
        # 分词
        print("  正在分词...")
        texts = df[text_column].fillna('').astype(str)
        texts_seg = [' '.join(jieba.cut(text)) for text in texts]
        
        # 计算TF-IDF
        print("  计算TF-IDF相似度...")
        vectorizer = TfidfVectorizer(max_features=100)
        tfidf_matrix = vectorizer.fit_transform(texts_seg)
        
        # 计算相似度（使用采样以加快速度）
        n_samples = len(df)
        sample_size = min(5000, n_samples)
        
        if n_samples > sample_size:
            print(f"  采样 {sample_size} 个样本计算相似度...")
            sample_idx = np.random.choice(n_samples, sample_size, replace=False)
            tfidf_sample = tfidf_matrix[sample_idx]
        else:
            sample_idx = np.arange(n_samples)
            tfidf_sample = tfidf_matrix
        
        similarity_matrix = cosine_similarity(tfidf_sample)
        
        # 构建图
        print("  构建网络图...")
        G = nx.Graph()
        
        # 添加节点
        for idx in sample_idx:
            G.add_node(idx)
        
        # 添加边（相似度超过阈值）
        edge_count = 0
        for i, idx_i in enumerate(sample_idx):
            for j, idx_j in enumerate(sample_idx):
                if i < j and similarity_matrix[i, j] >= threshold:
                    G.add_edge(idx_i, idx_j, weight=similarity_matrix[i, j])
                    edge_count += 1
        
        print(f"  ✅ 图构建完成")
        print(f"     节点数: {G.number_of_nodes()}")
        print(f"     边数: {G.number_of_edges()}")
        print(f"     平均度: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
        
        self.graph = G
        self.sample_idx = sample_idx
        return G
    
    def extract_graph_features(self, df):
        """
        从图中提取节点特征
        
        返回:
            DataFrame with graph features
        """
        print("\n【提取图特征】")
        
        if self.graph is None:
            print("  ⚠️ 图未构建，先构建图...")
            self.build_user_similarity_graph(df)
        
        G = self.graph
        n_samples = len(df)
        
        # 初始化特征字典
        features = {
            'degree': np.zeros(n_samples),  # 度中心性
            'clustering': np.zeros(n_samples),  # 聚类系数
            'pagerank': np.zeros(n_samples),  # PageRank
            'betweenness': np.zeros(n_samples),  # 介数中心性（采样）
            'closeness': np.zeros(n_samples),  # 接近中心性（采样）
            'eigenvector': np.zeros(n_samples),  # 特征向量中心性
        }
        
        # 1. 度中心性
        print("  计算度中心性...")
        degree_dict = dict(G.degree())
        for node, deg in degree_dict.items():
            features['degree'][node] = deg
        
        # 2. 聚类系数
        print("  计算聚类系数...")
        clustering_dict = nx.clustering(G)
        for node, clust in clustering_dict.items():
            features['clustering'][node] = clust
        
        # 3. PageRank
        print("  计算PageRank...")
        pagerank_dict = nx.pagerank(G, max_iter=50)
        for node, pr in pagerank_dict.items():
            features['pagerank'][node] = pr
        
        # 4. 特征向量中心性
        print("  计算特征向量中心性...")
        try:
            eigenvector_dict = nx.eigenvector_centrality(G, max_iter=100)
            for node, ev in eigenvector_dict.items():
                features['eigenvector'][node] = ev
        except:
            print("    ⚠️ 特征向量中心性计算失败")
        
        # 5. 介数中心性（采样计算，太慢了）
        print("  计算介数中心性（采样）...")
        if G.number_of_nodes() > 1000:
            sample_nodes = np.random.choice(list(G.nodes()), 
                                          min(500, G.number_of_nodes()), 
                                          replace=False)
            betweenness_dict = nx.betweenness_centrality(G, k=len(sample_nodes))
        else:
            betweenness_dict = nx.betweenness_centrality(G)
        for node, bc in betweenness_dict.items():
            features['betweenness'][node] = bc
        
        # 转换为DataFrame
        graph_df = pd.DataFrame(features)
        
        print(f"  ✅ 图特征提取完成")
        print(f"     特征维度: {graph_df.shape}")
        print(f"     特征列: {list(graph_df.columns)}")
        
        return graph_df


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
        'auc': roc_auc_score(y_test, y_proba),
        'threshold': threshold
    }
    
    return metrics, y_pred, y_proba


def plot_comparison(bert_metrics, gnn_metrics, save_path='gnn_improvement.png'):
    """绘制性能对比图"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 准备数据
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC']
    bert_values = [
        bert_metrics['accuracy'],
        bert_metrics['precision'],
        bert_metrics['recall'],
        bert_metrics['f1'],
        bert_metrics['auc']
    ]
    gnn_values = [
        gnn_metrics['accuracy'],
        gnn_metrics['precision'],
        gnn_metrics['recall'],
        gnn_metrics['f1'],
        gnn_metrics['auc']
    ]
    
    # 子图1：性能对比
    x = np.arange(len(metrics_names))
    width = 0.35
    
    bars1 = axes[0].bar(x - width/2, bert_values, width, 
                        label='BERT特征', alpha=0.8, color='#4ECDC4')
    bars2 = axes[0].bar(x + width/2, gnn_values, width, 
                        label='BERT+GNN', alpha=0.8, color='#95E1D3')
    axes[0].set_ylabel('分数', fontsize=12)
    axes[0].set_title('性能对比', fontsize=14, fontweight='bold')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics_names, rotation=45)
    axes[0].legend(fontsize=10)
    axes[0].set_ylim([0.7, 1.0])
    axes[0].grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, (v1, v2) in enumerate(zip(bert_values, gnn_values)):
        axes[0].text(i - width/2, v1 + 0.01, f'{v1:.3f}', 
                    ha='center', fontsize=9)
        axes[0].text(i + width/2, v2 + 0.01, f'{v2:.3f}', 
                    ha='center', fontsize=9, fontweight='bold')
    
    # 子图2：提升幅度
    improvements = [(g - b) * 100 for b, g in zip(bert_values, gnn_values)]
    colors = ['#2ECC71' if imp > 0 else '#E74C3C' for imp in improvements]
    
    bars = axes[1].bar(metrics_names, improvements, color=colors, alpha=0.7)
    axes[1].set_ylabel('提升幅度 (%)', fontsize=12)
    axes[1].set_title('GNN特征带来的提升', fontsize=14, fontweight='bold')
    axes[1].set_xticklabels(metrics_names, rotation=45)
    axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    axes[1].grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, (bar, imp) in enumerate(zip(bars, improvements)):
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., 
                    height + (0.2 if imp > 0 else -0.5), 
                    f'{imp:+.2f}%', ha='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"  ✅ 对比图已保存: {save_path}")
    plt.close()


def main():
    """主函数"""
    print_banner("步骤7：图神经网络特征融合", "🕸️")
    print("目标：F1分数从0.84提升到0.86+\n")
    
    # ==================== 阶段1：加载数据 ====================
    print("="*70)
    print("【阶段1】加载数据")
    print("="*70)
    
    # 加载原始数据
    try:
        df_original = pd.read_excel('data120.xlsx')
        print(f"✅ 原始数据: {df_original.shape[0]} 行")
    except:
        print("❌ 无法加载data120.xlsx")
        return
    
    # 加载BERT特征
    try:
        df_bert = pd.read_csv('features_with_bert.csv')
        print(f"✅ BERT特征: {df_bert.shape}")
    except:
        print("❌ 无法加载features_with_bert.csv")
        print("   请先运行: python step6_bert_boost.py")
        return
    
    # 获取标签
    if df_original['标注'].dtype == 'float64':
        y = df_original['标注'].fillna(0).astype(int)
    else:
        label_map = {'正常': 0, '水军': 1}
        y = df_original['标注'].map(label_map).values
    
    print(f"✅ 标签分布 - 正常: {sum(y==0)}, 水军: {sum(y==1)}")
    
    # ==================== 阶段2：提取图特征 ====================
    print("\n" + "="*70)
    print("【阶段2】提取图网络特征")
    print("="*70)
    
    graph_extractor = GraphFeatureExtractor()
    
    # 构建图并提取特征
    graph_extractor.build_user_similarity_graph(
        df_original, 
        text_column='评价内容',
        threshold=0.75
    )
    
    graph_features = graph_extractor.extract_graph_features(df_original)
    
    # 保存图特征
    graph_features.to_csv('graph_features.csv', index=False)
    print(f"\n✅ 图特征已保存: graph_features.csv")
    
    # ==================== 阶段3：特征融合 ====================
    print("\n" + "="*70)
    print("【阶段3】三重特征融合")
    print("="*70)
    
    print("  特征组成:")
    print(f"    1. 基础特征: 20 维")
    print(f"    2. BERT特征: 384 维")
    print(f"    3. 图特征: {graph_features.shape[1]} 维")
    
    # 合并所有特征
    X_all = pd.concat([
        df_bert.reset_index(drop=True),
        graph_features.reset_index(drop=True)
    ], axis=1)
    
    print(f"\n  融合后总特征: {X_all.shape[1]} 维")
    print(f"  ✅ 三重特征融合完成")
    
    # 保存融合特征
    X_all.to_csv('features_with_gnn.csv', index=False)
    print(f"  ✅ 融合特征已保存: features_with_gnn.csv")
    
    # ==================== 阶段4：数据划分 ====================
    print("\n" + "="*70)
    print("【阶段4】数据划分")
    print("="*70)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y, test_size=0.2, random_state=42, stratify=y
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
    
    # 实验1：BERT特征（基线）
    print("\n【实验1】BERT特征（基线）")
    print("-"*70)
    
    X_train_bert = X_train_scaled[:, :df_bert.shape[1]]
    X_test_bert = X_test_scaled[:, :df_bert.shape[1]]
    
    # 应用ADASYN
    adasyn = ADASYN(random_state=42, sampling_strategy=0.8)
    X_train_bert_res, y_train_res = adasyn.fit_resample(X_train_bert, y_train)
    
    model_bert = RandomForestClassifier(
        class_weight='balanced',
        max_depth=15,
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )
    
    print("  训练中...")
    model_bert.fit(X_train_bert_res, y_train_res)
    
    # 优化阈值
    y_train_proba = model_bert.predict_proba(X_train_bert_res)[:, 1]
    best_threshold_bert, _ = optimize_threshold(y_train_res, y_train_proba)
    
    bert_metrics, _, _ = evaluate_model(
        model_bert, X_test_bert, y_test, 
        "BERT", best_threshold_bert
    )
    
    print(f"\n  BERT模型性能:")
    print(f"    准确率: {bert_metrics['accuracy']:.4f}")
    print(f"    精确率: {bert_metrics['precision']:.4f}")
    print(f"    召回率: {bert_metrics['recall']:.4f}")
    print(f"    F1分数: {bert_metrics['f1']:.4f}")
    print(f"    AUC: {bert_metrics['auc']:.4f}")
    
    # 实验2：BERT + GNN特征
    print("\n【实验2】BERT + GNN特征")
    print("-"*70)
    
    # 应用ADASYN
    X_train_gnn_res, y_train_gnn_res = adasyn.fit_resample(X_train_scaled, y_train)
    
    model_gnn = RandomForestClassifier(
        class_weight='balanced',
        max_depth=15,
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )
    
    print("  训练中...")
    model_gnn.fit(X_train_gnn_res, y_train_gnn_res)
    
    # 优化阈值
    y_train_gnn_proba = model_gnn.predict_proba(X_train_gnn_res)[:, 1]
    best_threshold_gnn, best_f1 = optimize_threshold(y_train_gnn_res, y_train_gnn_proba)
    print(f"\n  最优阈值: {best_threshold_gnn:.3f}")
    print(f"  训练集最佳F1: {best_f1:.4f}")
    
    gnn_metrics, _, _ = evaluate_model(
        model_gnn, X_test_scaled, y_test,
        "BERT+GNN", best_threshold_gnn
    )
    
    print(f"\n  BERT+GNN模型性能:")
    print(f"    准确率: {gnn_metrics['accuracy']:.4f}")
    print(f"    精确率: {gnn_metrics['precision']:.4f}")
    print(f"    召回率: {gnn_metrics['recall']:.4f}")
    print(f"    F1分数: {gnn_metrics['f1']:.4f} 🎯")
    print(f"    AUC: {gnn_metrics['auc']:.4f}")
    
    # 计算提升幅度
    f1_improvement = (gnn_metrics['f1'] - bert_metrics['f1']) * 100
    print(f"\n  📈 F1分数提升: {f1_improvement:+.2f}%")
    
    # ==================== 阶段6：多模型对比 ====================
    print("\n" + "="*70)
    print("【阶段6】多模型对比（BERT+GNN特征）")
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
            n_estimators=300, random_state=42, n_jobs=-1
        ),
    }
    
    all_results = []
    
    for name, model in models_dict.items():
        print(f"\n训练 {name}...")
        model.fit(X_train_gnn_res, y_train_gnn_res)
        
        # 优化阈值
        y_train_proba = model.predict_proba(X_train_gnn_res)[:, 1]
        threshold, _ = optimize_threshold(y_train_gnn_res, y_train_proba)
        
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
    results_df.to_csv('gnn_models_comparison.csv', index=False)
    print(f"\n✅ 结果已保存: gnn_models_comparison.csv")
    
    # ==================== 阶段7：特征重要性分析 ====================
    print("\n" + "="*70)
    print("【阶段7】特征重要性分析")
    print("="*70)
    
    # 获取最佳模型
    best_model_name = results_df.iloc[0]['model']
    best_model = models_dict[best_model_name]
    
    # 提取特征重要性
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        feature_names = X_all.columns
        
        # 创建DataFrame
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        print("\nTop 20 最重要特征:")
        print(importance_df.head(20).to_string(index=False))
        
        # 保存
        importance_df.to_csv('gnn_feature_importance.csv', index=False)
        print(f"\n✅ 特征重要性已保存: gnn_feature_importance.csv")
        
        # 统计图特征的重要性
        graph_feature_names = graph_features.columns
        graph_importance = importance_df[
            importance_df['feature'].isin(graph_feature_names)
        ]['importance'].sum()
        
        print(f"\n📊 特征贡献度:")
        print(f"  基础特征贡献: {importance_df.iloc[:20]['importance'].sum():.4f}")
        print(f"  图特征总贡献: {graph_importance:.4f}")
        print(f"  图特征占比: {graph_importance/importances.sum()*100:.2f}%")
    
    # ==================== 阶段8：保存模型 ====================
    print("\n" + "="*70)
    print("【阶段8】保存最佳模型")
    print("="*70)
    
    # 保存模型和相关文件
    joblib.dump(best_model, f'best_model_gnn_{best_model_name}.pkl')
    joblib.dump(scaler, 'scaler_gnn.pkl')
    joblib.dump({'threshold': best_threshold_gnn}, 'threshold_gnn.pkl')
    
    print(f"  ✅ 最佳模型已保存: best_model_gnn_{best_model_name}.pkl")
    print(f"  ✅ Scaler已保存: scaler_gnn.pkl")
    print(f"  ✅ 阈值已保存: threshold_gnn.pkl")
    
    # ==================== 阶段9：生成可视化 ====================
    print("\n" + "="*70)
    print("【阶段9】生成可视化")
    print("="*70)
    
    plot_comparison(bert_metrics, gnn_metrics)
    
    # ==================== 总结 ====================
    print("\n" + "="*70)
    print("✅ 图神经网络特征融合完成！")
    print("="*70)
    
    print(f"\n🏆 最佳模型: {best_model_name}")
    print(f"   F1分数: {results_df.iloc[0]['f1']:.4f}")
    print(f"   准确率: {results_df.iloc[0]['accuracy']:.4f}")
    print(f"   AUC: {results_df.iloc[0]['auc']:.4f}")
    
    print(f"\n📈 性能演进:")
    print(f"   BERT F1: {bert_metrics['f1']:.4f}")
    print(f"   BERT+GNN F1: {gnn_metrics['f1']:.4f}")
    print(f"   提升幅度: {f1_improvement:+.2f}%")
    
    print(f"\n📁 生成的文件:")
    print(f"   • graph_features.csv - 图网络特征")
    print(f"   • features_with_gnn.csv - 完整融合特征")
    print(f"   • gnn_models_comparison.csv - 模型对比结果")
    print(f"   • gnn_feature_importance.csv - 特征重要性")
    print(f"   • best_model_gnn_{best_model_name}.pkl - 最佳模型")
    print(f"   • gnn_improvement.png - 性能对比图")
    
    print(f"\n🚀 下一步:")
    print(f"   生成完整分析报告:")
    print(f"   python step8_final_report.py")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()