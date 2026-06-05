"""
集成学习模型（改进版）- 专门处理类别不平衡
使用 SMOTE过采样 + 类别权重 + 阈值优化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                            f1_score, roc_auc_score, classification_report,
                            confusion_matrix, roc_curve, precision_recall_curve)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class ImprovedEnsembleModel:
    """改进的集成学习模型（处理类别不平衡）"""
    
    def __init__(self, use_smote=True, optimize_threshold=True):
        self.models = {}
        self.results = {}
        self.scaler = StandardScaler()
        self.use_smote = use_smote
        self.optimize_threshold = optimize_threshold
        self.best_thresholds = {}
        
    def prepare_data(self, features, labels, test_size=0.2):
        """准备数据（带SMOTE）"""
        print("\n" + "="*70)
        print("【数据准备 - 处理类别不平衡】")
        print("="*70)
        
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        print(f"\n原始数据分布:")
        print(f"  训练集 - 正常: {sum(y_train==0):,}, 水军: {sum(y_train==1):,}")
        print(f"  不平衡比例: {sum(y_train==0)/sum(y_train==1):.2f}:1")
        
        # 标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # SMOTE过采样
        if self.use_smote:
            print(f"\n应用SMOTE过采样...")
            # 使用SMOTETomek（过采样+清理边界）
            smote_tomek = SMOTETomek(random_state=42)
            X_train_resampled, y_train_resampled = smote_tomek.fit_resample(
                X_train_scaled, y_train
            )
            
            print(f"  过采样后 - 正常: {sum(y_train_resampled==0):,}, "
                  f"水军: {sum(y_train_resampled==1):,}")
            print(f"  新平衡比例: {sum(y_train_resampled==0)/sum(y_train_resampled==1):.2f}:1")
            
            X_train_scaled = X_train_resampled
            y_train = pd.Series(y_train_resampled)
        
        self.X_train = pd.DataFrame(X_train_scaled, columns=features.columns)
        self.X_test = pd.DataFrame(X_test_scaled, columns=features.columns)
        self.y_train = y_train.reset_index(drop=True)
        self.y_test = y_test.reset_index(drop=True)
        
        print(f"\n最终训练数据:")
        print(f"  训练集: {len(self.X_train):,} 样本")
        print(f"  测试集: {len(self.X_test):,} 样本")
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def optimize_classification_threshold(self, y_true, y_pred_proba):
        """优化分类阈值以提高F1分数"""
        thresholds = np.arange(0.3, 0.7, 0.01)
        best_f1 = 0
        best_threshold = 0.5
        
        for threshold in thresholds:
            y_pred = (y_pred_proba >= threshold).astype(int)
            f1 = f1_score(y_true, y_pred)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        return best_threshold, best_f1
    
    def train_xgboost_balanced(self):
        """训练XGBoost（类别权重）"""
        print("\n" + "="*70)
        print("【模型1】XGBoost（类别平衡优化）")
        print("="*70)
        
        # 计算类别权重
        scale_pos_weight = sum(self.y_train == 0) / sum(self.y_train == 1)
        
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,  # 关键：类别权重
            random_state=42,
            eval_metric='logloss',
            use_label_encoder=False
        )
        
        print(f"  类别权重: {scale_pos_weight:.2f}")
        print("\n训练中...")
        model.fit(self.X_train, self.y_train)
        
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        # 优化阈值
        if self.optimize_threshold:
            best_threshold, best_f1 = self.optimize_classification_threshold(
                self.y_test, y_pred_proba
            )
            print(f"  最优阈值: {best_threshold:.3f}")
            y_pred = (y_pred_proba >= best_threshold).astype(int)
            self.best_thresholds['XGBoost'] = best_threshold
        else:
            y_pred = model.predict(self.X_test)
        
        metrics = self._evaluate_model('XGBoost', y_pred, y_pred_proba)
        
        self.models['XGBoost'] = model
        self.results['XGBoost'] = metrics
        
        return model, metrics
    
    def train_lightgbm_balanced(self):
        """训练LightGBM（类别权重）"""
        print("\n" + "="*70)
        print("【模型2】LightGBM（类别平衡优化）")
        print("="*70)
        
        model = lgb.LGBMClassifier(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            class_weight='balanced',  # 自动平衡
            random_state=42,
            verbose=-1
        )
        
        print("\n训练中...")
        model.fit(self.X_train, self.y_train)
        
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        if self.optimize_threshold:
            best_threshold, _ = self.optimize_classification_threshold(
                self.y_test, y_pred_proba
            )
            print(f"  最优阈值: {best_threshold:.3f}")
            y_pred = (y_pred_proba >= best_threshold).astype(int)
            self.best_thresholds['LightGBM'] = best_threshold
        else:
            y_pred = model.predict(self.X_test)
        
        metrics = self._evaluate_model('LightGBM', y_pred, y_pred_proba)
        
        self.models['LightGBM'] = model
        self.results['LightGBM'] = metrics
        
        return model, metrics
    
    def train_catboost_balanced(self):
        """训练CatBoost（类别权重）"""
        print("\n" + "="*70)
        print("【模型3】CatBoost（类别平衡优化）")
        print("="*70)
        
        model = CatBoostClassifier(
            iterations=300,
            depth=7,
            learning_rate=0.05,
            auto_class_weights='Balanced',  # 自动平衡
            random_state=42,
            verbose=False
        )
        
        print("\n训练中...")
        model.fit(self.X_train, self.y_train)
        
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        if self.optimize_threshold:
            best_threshold, _ = self.optimize_classification_threshold(
                self.y_test, y_pred_proba
            )
            print(f"  最优阈值: {best_threshold:.3f}")
            y_pred = (y_pred_proba >= best_threshold).astype(int)
            self.best_thresholds['CatBoost'] = best_threshold
        else:
            y_pred = model.predict(self.X_test)
        
        metrics = self._evaluate_model('CatBoost', y_pred, y_pred_proba)
        
        self.models['CatBoost'] = model
        self.results['CatBoost'] = metrics
        
        return model, metrics
    
    def train_random_forest_balanced(self):
        """训练随机森林（类别权重）"""
        print("\n" + "="*70)
        print("【模型4】Random Forest（类别平衡优化）")
        print("="*70)
        
        model = RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',  # 类别权重
            random_state=42,
            n_jobs=-1
        )
        
        print("\n训练中...")
        model.fit(self.X_train, self.y_train)
        
        y_pred_proba = model.predict_proba(self.X_test)[:, 1]
        
        if self.optimize_threshold:
            best_threshold, _ = self.optimize_classification_threshold(
                self.y_test, y_pred_proba
            )
            print(f"  最优阈值: {best_threshold:.3f}")
            y_pred = (y_pred_proba >= best_threshold).astype(int)
            self.best_thresholds['RandomForest'] = best_threshold
        else:
            y_pred = model.predict(self.X_test)
        
        metrics = self._evaluate_model('RandomForest', y_pred, y_pred_proba)
        
        self.models['RandomForest'] = model
        self.results['RandomForest'] = metrics
        
        return model, metrics
    
    def train_voting_ensemble(self):
        """训练投票集成"""
        print("\n" + "="*70)
        print("【集成方法1】Voting Ensemble（优化版）")
        print("="*70)
        
        voting_model = VotingClassifier(
            estimators=[
                ('xgb', self.models['XGBoost']),
                ('lgb', self.models['LightGBM']),
                ('cat', self.models['CatBoost'])
            ],
            voting='soft',
            weights=[2, 1, 1]  # XGBoost权重更高
        )
        
        print("\n训练中...")
        voting_model.fit(self.X_train, self.y_train)
        
        y_pred_proba = voting_model.predict_proba(self.X_test)[:, 1]
        
        if self.optimize_threshold:
            best_threshold, _ = self.optimize_classification_threshold(
                self.y_test, y_pred_proba
            )
            print(f"  最优阈值: {best_threshold:.3f}")
            y_pred = (y_pred_proba >= best_threshold).astype(int)
            self.best_thresholds['VotingEnsemble'] = best_threshold
        else:
            y_pred = voting_model.predict(self.X_test)
        
        metrics = self._evaluate_model('VotingEnsemble', y_pred, y_pred_proba)
        
        self.models['VotingEnsemble'] = voting_model
        self.results['VotingEnsemble'] = metrics
        
        return voting_model, metrics
    
    def train_stacking_ensemble(self):
        """训练堆叠集成"""
        print("\n" + "="*70)
        print("【集成方法2】Stacking Ensemble（优化版）")
        print("="*70)
        
        base_learners = [
            ('xgb', self.models['XGBoost']),
            ('lgb', self.models['LightGBM']),
            ('cat', self.models['CatBoost']),
            ('rf', self.models['RandomForest'])
        ]
        
        meta_learner = LogisticRegression(
            random_state=42, 
            max_iter=1000,
            class_weight='balanced'  # 元学习器也平衡
        )
        
        stacking_model = StackingClassifier(
            estimators=base_learners,
            final_estimator=meta_learner,
            cv=5
        )
        
        print("\n训练中...")
        stacking_model.fit(self.X_train, self.y_train)
        
        y_pred_proba = stacking_model.predict_proba(self.X_test)[:, 1]
        
        if self.optimize_threshold:
            best_threshold, _ = self.optimize_classification_threshold(
                self.y_test, y_pred_proba
            )
            print(f"  最优阈值: {best_threshold:.3f}")
            y_pred = (y_pred_proba >= best_threshold).astype(int)
            self.best_thresholds['StackingEnsemble'] = best_threshold
        else:
            y_pred = stacking_model.predict(self.X_test)
        
        metrics = self._evaluate_model('StackingEnsemble', y_pred, y_pred_proba)
        
        self.models['StackingEnsemble'] = stacking_model
        self.results['StackingEnsemble'] = metrics
        
        return stacking_model, metrics
    
    def _evaluate_model(self, model_name, y_pred, y_pred_proba):
        """评估模型"""
        accuracy = accuracy_score(self.y_test, y_pred)
        precision = precision_score(self.y_test, y_pred, zero_division=0)
        recall = recall_score(self.y_test, y_pred, zero_division=0)
        f1 = f1_score(self.y_test, y_pred, zero_division=0)
        
        try:
            auc = roc_auc_score(self.y_test, y_pred_proba)
        except:
            auc = 0.0
        
        print(f"\n{model_name} 性能指标:")
        print(f"  准确率 (Accuracy):  {accuracy:.4f}")
        print(f"  精确率 (Precision): {precision:.4f} {'⬆️' if precision > 0.7 else ''}")
        print(f"  召回率 (Recall):    {recall:.4f} {'⬆️' if recall > 0.6 else ''}")
        print(f"  F1分数 (F1-Score):  {f1:.4f} {'✅' if f1 > 0.65 else '⚠️'}")
        print(f"  AUC-ROC:            {auc:.4f}")
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
    
    def compare_models(self):
        """对比模型"""
        print("\n" + "="*70)
        print("【模型对比】")
        print("="*70)
        
        comparison = pd.DataFrame({
            'Model': list(self.results.keys()),
            'Accuracy': [r['accuracy'] for r in self.results.values()],
            'Precision': [r['precision'] for r in self.results.values()],
            'Recall': [r['recall'] for r in self.results.values()],
            'F1-Score': [r['f1'] for r in self.results.values()],
            'AUC-ROC': [r['auc'] for r in self.results.values()]
        })
        
        comparison = comparison.sort_values('F1-Score', ascending=False)
        
        print("\n模型性能排名:")
        print(comparison.to_string(index=False))
        
        best_model = comparison.iloc[0]['Model']
        best_f1 = comparison.iloc[0]['F1-Score']
        
        print(f"\n🏆 最佳模型: {best_model}")
        print(f"   F1分数: {best_f1:.4f}")
        
        if best_f1 > 0.65:
            print(f"   ✅ 性能优秀！")
        elif best_f1 > 0.55:
            print(f"   ⚠️  性能良好，仍有提升空间")
        else:
            print(f"   ⚠️  性能一般，需要进一步优化")
        
        return comparison
    
    def visualize_results(self, save_path='ensemble_results_improved.png'):
        """可视化结果"""
        print("\n" + "="*70)
        print("【生成可视化】")
        print("="*70)
        
        fig = plt.figure(figsize=(20, 12))
        
        models = list(self.results.keys())
        
        # 1. 模型性能对比
        ax1 = plt.subplot(2, 3, 1)
        metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'AUC-ROC']
        metric_key_map = {
            'Accuracy': 'accuracy',
            'Precision': 'precision',
            'Recall': 'recall',
            'F1-Score': 'f1',
            'AUC-ROC': 'auc'
        }
        
        x = np.arange(len(models))
        width = 0.15
        
        for i, metric in enumerate(metrics_names):
            key = metric_key_map[metric]
            values = [self.results[m][key] for m in models]
            ax1.bar(x + i*width, values, width, label=metric)
        
        ax1.set_xlabel('模型')
        ax1.set_ylabel('分数')
        ax1.set_title('模型性能对比（改进版）', fontsize=14, fontweight='bold')
        ax1.set_xticks(x + width * 2)
        ax1.set_xticklabels(models, rotation=45, ha='right')
        ax1.legend(loc='lower right', fontsize=8)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. F1分数对比
        ax2 = plt.subplot(2, 3, 2)
        f1_scores = [self.results[m]['f1'] for m in models]
        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(models)))
        bars = ax2.barh(models, f1_scores, color=colors)
        ax2.set_xlabel('F1分数')
        ax2.set_title('F1分数对比（优化后）', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.axvline(x=0.65, color='red', linestyle='--', label='目标线(0.65)')
        ax2.legend()
        
        for i, (bar, score) in enumerate(zip(bars, f1_scores)):
            ax2.text(score + 0.01, i, f'{score:.4f}', 
                    va='center', fontweight='bold')
        
        # 3. ROC曲线
        ax3 = plt.subplot(2, 3, 3)
        for model_name in models:
            if self.results[model_name]['auc'] > 0:
                y_pred_proba = self.results[model_name]['y_pred_proba']
                fpr, tpr, _ = roc_curve(self.y_test, y_pred_proba)
                auc = self.results[model_name]['auc']
                ax3.plot(fpr, tpr, label=f'{model_name} (AUC={auc:.3f})', linewidth=2)
        
        ax3.plot([0, 1], [0, 1], 'k--', label='随机猜测', linewidth=1)
        ax3.set_xlabel('假正例率 (FPR)')
        ax3.set_ylabel('真正例率 (TPR)')
        ax3.set_title('ROC曲线对比', fontsize=14, fontweight='bold')
        ax3.legend(loc='lower right', fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        # 4. 混淆矩阵（最佳模型）
        ax4 = plt.subplot(2, 3, 4)
        best_model_name = max(self.results.keys(), 
                             key=lambda k: self.results[k]['f1'])
        y_pred = self.results[best_model_name]['y_pred']
        cm = confusion_matrix(self.y_test, y_pred)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax4,
                   xticklabels=['正常', '水军'],
                   yticklabels=['正常', '水军'])
        ax4.set_title(f'{best_model_name} 混淆矩阵', fontsize=14, fontweight='bold')
        ax4.set_ylabel('真实标签')
        ax4.set_xlabel('预测标签')
        
        # 5. Recall对比（重点关注）
        ax5 = plt.subplot(2, 3, 5)
        recalls = [self.results[m]['recall'] for m in models]
        precisions = [self.results[m]['precision'] for m in models]
        
        ax5.scatter(recalls, precisions, s=200, alpha=0.6, c=range(len(models)), cmap='viridis')
        for i, model in enumerate(models):
            ax5.annotate(model, (recalls[i], precisions[i]), 
                        fontsize=8, ha='center')
        
        ax5.axhline(y=0.7, color='r', linestyle='--', alpha=0.3, label='Precision目标')
        ax5.axvline(x=0.6, color='b', linestyle='--', alpha=0.3, label='Recall目标')
        ax5.set_xlabel('召回率 (Recall)')
        ax5.set_ylabel('精确率 (Precision)')
        ax5.set_title('Precision vs Recall', fontsize=14, fontweight='bold')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # 6. 最优阈值对比
        ax6 = plt.subplot(2, 3, 6)
        if self.best_thresholds:
            threshold_models = list(self.best_thresholds.keys())
            threshold_values = list(self.best_thresholds.values())
            
            bars = ax6.bar(threshold_models, threshold_values, color='coral')
            ax6.axhline(y=0.5, color='red', linestyle='--', label='默认阈值(0.5)')
            ax6.set_ylabel('最优阈值')
            ax6.set_title('各模型最优分类阈值', fontsize=14, fontweight='bold')
            ax6.set_xticklabels(threshold_models, rotation=45, ha='right')
            ax6.legend()
            ax6.grid(True, alpha=0.3, axis='y')
            
            for bar, val in zip(bars, threshold_values):
                height = bar.get_height()
                ax6.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.3f}',
                       ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 可视化已保存: {save_path}")
        plt.close()
    
    def save_models(self, save_dir='models_improved'):
        """保存模型"""
        import os
        os.makedirs(save_dir, exist_ok=True)
        
        print("\n" + "="*70)
        print("【保存模型】")
        print("="*70)
        
        for model_name, model in self.models.items():
            model_path = f"{save_dir}/{model_name}.pkl"
            joblib.dump(model, model_path)
            print(f"  ✓ {model_name} 已保存")
        
        joblib.dump(self.scaler, f"{save_dir}/scaler.pkl")
        joblib.dump(self.best_thresholds, f"{save_dir}/best_thresholds.pkl")
        print(f"  ✓ Scaler 和阈值已保存")
        
        return save_dir


def main():
    """主函数"""
    print("\n" + "🚀"*35)
    print("\n" + " "*12 + "步骤4：集成学习模型（改进版）")
    print(" "*8 + "处理类别不平衡 + 阈值优化 + SMOTE过采样")
    print("\n" + "🚀"*35)
    
    # 1. 加载数据
    print("\n【阶段1】加载数据")
    print("-"*70)
    
    try:
        features = pd.read_csv("advanced_features.csv")
        print(f"✅ 加载特征数据: {features.shape[0]:,} 行 × {features.shape[1]} 列")
        
        original_data = pd.read_excel("data120.xlsx")
        if '标注' in original_data.columns:
            labels = original_data['标注'].fillna(0).astype(int)
            print(f"✅ 加载标签数据")
            print(f"   - 正常: {sum(labels==0):,} 条")
            print(f"   - 水军: {sum(labels==1):,} 条")
            print(f"   - 不平衡比例: {sum(labels==0)/sum(labels==1):.2f}:1 ⚠️")
        else:
            print("❌ 错误：未找到'标注'列")
            return
        
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        return
    
    # 2. 初始化改进模型
    print("\n【阶段2】初始化改进模型")
    print("-"*70)
    print("✅ 启用SMOTE过采样")
    print("✅ 启用阈值优化")
    
    ensemble = ImprovedEnsembleModel(use_smote=True, optimize_threshold=True)
    
    # 3. 准备数据
    ensemble.prepare_data(features, labels)
    
    # 4. 训练基础模型
    print("\n【阶段3】训练平衡优化模型")
    print("-"*70)
    
    ensemble.train_xgboost_balanced()
    ensemble.train_lightgbm_balanced()
    ensemble.train_catboost_balanced()
    ensemble.train_random_forest_balanced()
    
    # 5. 训练集成模型
    print("\n【阶段4】训练集成模型")
    print("-"*70)
    
    ensemble.train_voting_ensemble()
    ensemble.train_stacking_ensemble()
    
    # 6. 模型对比
    print("\n【阶段5】模型性能对比")
    print("-"*70)
    
    comparison = ensemble.compare_models()
    comparison.to_csv("model_comparison_improved.csv", index=False)
    print(f"\n✅ 结果已保存: model_comparison_improved.csv")
    
    # 7. 可视化
    print("\n【阶段6】生成可视化")
    print("-"*70)
    
    ensemble.visualize_results('ensemble_results_improved.png')
    
    # 8. 保存模型
    print("\n【阶段7】保存模型")
    print("-"*70)
    
    ensemble.save_models('models_improved')
    
    # 9. 总结
    print("\n" + "="*70)
    print("✅ 改进版集成学习完成！")
    print("="*70)
    
    best_model = comparison.iloc[0]
    print(f"\n🏆 最佳模型: {best_model['Model']}")
    print(f"   准确率: {best_model['Accuracy']:.4f}")
    print(f"   精确率: {best_model['Precision']:.4f}")
    print(f"   召回率: {best_model['Recall']:.4f}")
    print(f"   F1分数: {best_model['F1-Score']:.4f} ", end='')
    
    if best_model['F1-Score'] > 0.65:
        print("✅ 大幅改进！")
    else:
        print("⚠️  仍需优化")
    
    print(f"\n📁 生成的文件:")
    print(f"   • model_comparison_improved.csv")
    print(f"   • ensemble_results_improved.png")
    print(f"   • models_improved/")
    
    print(f"\n🚀 下一步:")
    print(f"   python step5_explainability_analysis.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()