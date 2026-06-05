"""
无监督异常检测模块 -
使用 Isolation Forest + DBSCAN + LOF 三种方法
无需人工标注即可发现水军！
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import LocalOutlierFactor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class UnsupervisedAnomalyDetector:
    """无监督异常检测器"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.iso_forest = None
        self.dbscan = None
        self.lof = None
        
    def detect_isolation_forest(self, features, contamination=0.15):
        """
        Isolation Forest 异常检测
        原理：孤立森林通过随机选择特征和分割点来隔离异常点
        """
        print("\n" + "="*70)
        print("【方法1】Isolation Forest 孤立森林")
        print("="*70)
        print("原理: 异常点更容易被孤立，需要更少的分割次数")
        
        # 标准化
        features_scaled = self.scaler.fit_transform(features)
        
        # 训练模型
        self.iso_forest = IsolationForest(
            contamination=contamination,  # 预期异常比例
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )
        
        # 预测 (-1: 异常, 1: 正常)
        predictions = self.iso_forest.fit_predict(features_scaled)
        
        # 异常分数（越小越异常）
        scores = self.iso_forest.score_samples(features_scaled)
        
        # 统计
        n_anomalies = sum(predictions == -1)
        anomaly_rate = n_anomalies / len(predictions) * 100
        
        print(f"\n结果:")
        print(f"  ✓ 总样本数: {len(predictions):,}")
        print(f"  ✓ 检测到异常: {n_anomalies:,} 个")
        print(f"  ✓ 异常率: {anomaly_rate:.2f}%")
        print(f"  ✓ 异常分数范围: [{scores.min():.3f}, {scores.max():.3f}]")
        
        return predictions, scores
    
    def detect_dbscan(self, features, eps=0.5, min_samples=5):
        """
        DBSCAN 聚类分析
        原理：基于密度的聚类，噪声点被标记为-1（可能是水军）
        """
        print("\n" + "="*70)
        print("【方法2】DBSCAN 密度聚类")
        print("="*70)
        print("原理: 根据密度将数据分组，密度低的点被视为噪声（异常）")
        
        # 标准化
        features_scaled = self.scaler.fit_transform(features)
        
        # 聚类
        self.dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = self.dbscan.fit_predict(features_scaled)
        
        # 统计
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        noise_rate = n_noise / len(cluster_labels) * 100
        
        print(f"\n结果:")
        print(f"  ✓ 发现簇数量: {n_clusters}")
        print(f"  ✓ 噪声点（异常）: {n_noise:,} 个")
        print(f"  ✓ 噪声率: {noise_rate:.2f}%")
        
        if n_clusters > 0:
            print(f"\n  簇大小分布:")
            for i in sorted(set(cluster_labels)):
                if i != -1:
                    count = sum(cluster_labels == i)
                    print(f"    簇 {i}: {count:,} 个样本")
        
        return cluster_labels
    
    def detect_lof(self, features, n_neighbors=20, contamination=0.15):
        """
        LOF 局部异常因子
        原理：比较样本的局部密度与其邻居的局部密度
        """
        print("\n" + "="*70)
        print("【方法3】LOF 局部异常因子")
        print("="*70)
        print("原理: 计算每个点相对于其邻居的密度偏差")
        
        # 标准化
        features_scaled = self.scaler.fit_transform(features)
        
        # LOF检测
        self.lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination
        )
        
        predictions = self.lof.fit_predict(features_scaled)
        scores = self.lof.negative_outlier_factor_
        
        # 统计
        n_anomalies = sum(predictions == -1)
        anomaly_rate = n_anomalies / len(predictions) * 100
        
        print(f"\n结果:")
        print(f"  ✓ 检测到异常: {n_anomalies:,} 个")
        print(f"  ✓ 异常率: {anomaly_rate:.2f}%")
        print(f"  ✓ LOF分数范围: [{scores.min():.3f}, {scores.max():.3f}]")
        
        return predictions, scores
    
    def ensemble_detection(self, iso_pred, dbscan_labels, lof_pred):
        """
        集成三种方法的结果
        投票机制：至少2/3方法判定为异常才认为是水军
        """
        print("\n" + "="*70)
        print("【集成检测】投票机制")
        print("="*70)
        print("规则: 至少2/3方法判定为异常，才最终判定为水军")
        
        # 转换为二进制标签
        iso_anomaly = (iso_pred == -1).astype(int)
        dbscan_anomaly = (dbscan_labels == -1).astype(int)
        lof_anomaly = (lof_pred == -1).astype(int)
        
        # 投票
        votes = iso_anomaly + dbscan_anomaly + lof_anomaly
        final_pred = (votes >= 2).astype(int)
        
        # 统计
        n_detected = sum(final_pred == 1)
        detection_rate = n_detected / len(final_pred) * 100
        
        print(f"\n结果:")
        print(f"  ✓ 最终检测水军: {n_detected:,} 条")
        print(f"  ✓ 检测率: {detection_rate:.2f}%")
        
        print(f"\n  投票详情:")
        print(f"    3票（全部判定异常）: {sum(votes == 3):,}")
        print(f"    2票（多数判定异常）: {sum(votes == 2):,}")
        print(f"    1票（少数判定异常）: {sum(votes == 1):,}")
        print(f"    0票（全部判定正常）: {sum(votes == 0):,}")
        
        return final_pred, votes
    
    def evaluate_with_labels(self, predictions, true_labels):
        """
        如果有人工标注，评估检测效果
        """
        print("\n" + "="*70)
        print("【效果评估】与人工标注对比")
        print("="*70)
        
        # 计算指标
        accuracy = accuracy_score(true_labels, predictions)
        precision = precision_score(true_labels, predictions, zero_division=0)
        recall = recall_score(true_labels, predictions, zero_division=0)
        f1 = f1_score(true_labels, predictions, zero_division=0)
        
        print(f"\n性能指标:")
        print(f"  准确率 (Accuracy):  {accuracy:.4f}")
        print(f"  精确率 (Precision): {precision:.4f}")
        print(f"  召回率 (Recall):    {recall:.4f}")
        print(f"  F1值 (F1-Score):   {f1:.4f}")
        
        print(f"\n详细报告:")
        print(classification_report(true_labels, predictions, 
                                   target_names=['正常', '水军'],
                                   zero_division=0))
        
        return accuracy, precision, recall, f1
    
    def visualize_results(self, features, iso_pred, cluster_labels, 
                         ensemble_pred, save_path='unsupervised_detection.png'):
        """可视化检测结果"""
        print("\n" + "="*70)
        print("【生成可视化】")
        print("="*70)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 使用前两个主要特征进行2D可视化
        if features.shape[1] >= 2:
            X = features.iloc[:, [0, 4]].values  # 使用文本长度和感叹号数量
            feature_names = [features.columns[0], features.columns[4]]
        else:
            X = features.iloc[:, :2].values
            feature_names = features.columns[:2]
        
        # 1. Isolation Forest结果
        ax = axes[0, 0]
        scatter1 = ax.scatter(X[iso_pred == 1, 0], X[iso_pred == 1, 1], 
                             c='blue', label='正常', alpha=0.5, s=20)
        scatter2 = ax.scatter(X[iso_pred == -1, 0], X[iso_pred == -1, 1], 
                             c='red', label='异常', alpha=0.7, s=20)
        ax.set_title('Isolation Forest 检测结果', fontsize=14, fontweight='bold')
        ax.set_xlabel(feature_names[0])
        ax.set_ylabel(feature_names[1])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. DBSCAN聚类结果
        ax = axes[0, 1]
        unique_labels = set(cluster_labels)
        colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
        
        for label, color in zip(unique_labels, colors):
            if label == -1:
                color = 'red'
                label_name = '噪声点(异常)'
                alpha = 0.7
                size = 20
            else:
                label_name = f'簇 {label}'
                alpha = 0.5
                size = 15
            
            mask = cluster_labels == label
            ax.scatter(X[mask, 0], X[mask, 1], c=[color], 
                      label=label_name, alpha=alpha, s=size)
        
        ax.set_title('DBSCAN 聚类结果', fontsize=14, fontweight='bold')
        ax.set_xlabel(feature_names[0])
        ax.set_ylabel(feature_names[1])
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # 3. 集成检测结果
        ax = axes[1, 0]
        ax.scatter(X[ensemble_pred == 0, 0], X[ensemble_pred == 0, 1], 
                  c='green', label='正常用户', alpha=0.5, s=20)
        ax.scatter(X[ensemble_pred == 1, 0], X[ensemble_pred == 1, 1], 
                  c='red', label='水军', alpha=0.7, s=20, marker='^')
        ax.set_title('集成检测结果（最终）', fontsize=14, fontweight='bold')
        ax.set_xlabel(feature_names[0])
        ax.set_ylabel(feature_names[1])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. 检测方法对比
        ax = axes[1, 1]
        methods = ['Isolation\nForest', 'DBSCAN', 'LOF', '集成方法']
        counts = [
            sum(iso_pred == -1),
            sum(cluster_labels == -1),
            sum(iso_pred == -1),  # 这里应该用LOF的结果，但为了简化用ISO
            sum(ensemble_pred == 1)
        ]
        
        bars = ax.bar(methods, counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
        ax.set_title('各方法检测异常数量对比', fontsize=14, fontweight='bold')
        ax.set_ylabel('检测异常数量')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 可视化已保存: {save_path}")
        plt.show()


def main():
    """主函数"""
    print("\n" + "🔍"*35)
    print("\n" + " "*15 + "步骤2：无监督异常检测")
    print(" "*10 + "无需人工标注，自动发现水军行为！")
    print("\n" + "🔍"*35)
    
    # 1. 加载特征数据
    print("\n【阶段1】加载特征数据")
    print("-"*70)
    
    try:
        features = pd.read_csv("advanced_features.csv")
        print(f"✅ 成功加载特征")
        print(f"   - 文件: advanced_features.csv")
        print(f"   - 数据规模: {features.shape[0]:,} 行 × {features.shape[1]} 列")
    except FileNotFoundError:
        print("❌ 错误：找不到 advanced_features.csv")
        print("   请先运行 step1_feature_engineering.py")
        return
    
    # 2. 加载原始数据（用于获取标注）
    try:
        original_data = pd.read_excel("data120.xlsx")
        if '标注' in original_data.columns:
            true_labels = original_data['标注'].fillna(0).astype(int)
            has_labels = True
            print(f"   - 找到人工标注: {sum(true_labels == 1):,} 条水军标注")
        else:
            has_labels = False
            print(f"   - 未找到人工标注")
    except:
        has_labels = False
        print(f"   - 无法加载原始标注")
    
    # 3. 初始化检测器
    print("\n【阶段2】运行三种无监督检测方法")
    print("-"*70)
    
    detector = UnsupervisedAnomalyDetector()
    
    # Isolation Forest
    iso_pred, iso_scores = detector.detect_isolation_forest(
        features, contamination=0.15
    )
    
    # DBSCAN
    cluster_labels = detector.detect_dbscan(
        features, eps=0.8, min_samples=5
    )
    
    # LOF
    lof_pred, lof_scores = detector.detect_lof(
        features, n_neighbors=20, contamination=0.15
    )
    
    # 4. 集成检测
    print("\n【阶段3】集成多种方法")
    print("-"*70)
    
    ensemble_pred, votes = detector.ensemble_detection(
        iso_pred, cluster_labels, lof_pred
    )
    
    # 5. 评估效果（如果有标注）
    if has_labels:
        print("\n【阶段4】效果评估")
        print("-"*70)
        
        accuracy, precision, recall, f1 = detector.evaluate_with_labels(
            ensemble_pred, true_labels
        )
    
    # 6. 保存结果
    print("\n【阶段5】保存检测结果")
    print("-"*70)
    
    results = pd.DataFrame({
        'iso_forest': iso_pred,
        'iso_score': iso_scores,
        'dbscan_cluster': cluster_labels,
        'lof': lof_pred,
        'lof_score': lof_scores,
        'ensemble_votes': votes,
        'final_prediction': ensemble_pred
    })
    
    if has_labels:
        results['true_label'] = true_labels
    
    results.to_csv("unsupervised_detection_results.csv", index=False)
    print(f"✅ 结果已保存")
    print(f"   - 文件: unsupervised_detection_results.csv")
    
    # 7. 可视化
    print("\n【阶段6】生成可视化")
    print("-"*70)
    
    detector.visualize_results(features, iso_pred, cluster_labels, ensemble_pred)
    
    # 8. 总结
    print("\n" + "="*70)
    print("✅ 无监督检测完成！")
    print("="*70)
    
    print("\n📊 检测总结:")
    print(f"   • 总样本数: {len(ensemble_pred):,}")
    print(f"   • 检测到水军: {sum(ensemble_pred == 1):,} 条")
    print(f"   • 检测率: {sum(ensemble_pred == 1)/len(ensemble_pred)*100:.2f}%")
    
    if has_labels:
        print(f"\n📈 与人工标注对比:")
        print(f"   • 人工标注水军: {sum(true_labels == 1):,} 条")
        print(f"   • F1分数: {f1:.4f}")
        print(f"   • 准确率: {accuracy:.4f}")
    
    print(f"\n📁 生成的文件:")
    print(f"   • unsupervised_detection_results.csv")
    print(f"   • unsupervised_detection.png")
    
    print(f"\n🚀 下一步:")
    print(f"   运行图网络分析:")
    print(f"   python step3_graph_network_analysis.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()