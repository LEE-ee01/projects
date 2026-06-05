"""
可解释性分析模块
使用 SHAP + LIME 解释模型决策
生成详细的水军检测报告
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from lime import lime_tabular
import joblib
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class ExplainabilityAnalyzer:
    """可解释性分析器"""
    
    def __init__(self, model_path='models_improved'):
        self.model_path = model_path
        self.models = {}
        self.scaler = None
        self.best_model = None
        self.X_test = None
        self.y_test = None
        self.feature_names = None
        
    def load_models(self):
        """加载训练好的模型"""
        print("\n" + "="*70)
        print("【加载模型】")
        print("="*70)
        
        try:
            self.scaler = joblib.load(f'{self.model_path}/scaler.pkl')
            print(f"✅ 加载 Scaler")
            
            model_names = ['XGBoost', 'LightGBM', 'CatBoost', 
                          'RandomForest', 'StackingEnsemble']
            
            for name in model_names:
                try:
                    model = joblib.load(f'{self.model_path}/{name}.pkl')
                    self.models[name] = model
                    print(f"✅ 加载 {name}")
                except:
                    print(f"⚠️  未找到 {name}")
            
            # 选择XGBoost作为主要解释对象（通常是最佳模型）
            if 'XGBoost' in self.models:
                self.best_model = self.models['XGBoost']
                print(f"\n🏆 选择 XGBoost 进行详细分析")
            
            return True
            
        except Exception as e:
            print(f"❌ 加载模型失败: {e}")
            return False
    
    def load_test_data(self):
        """加载测试数据"""
        print("\n" + "="*70)
        print("【加载测试数据】")
        print("="*70)
        
        try:
            # 加载特征
            features = pd.read_csv("advanced_features.csv")
            print(f"✅ 加载特征数据: {features.shape[0]:,} 行")
            
            # 加载标签
            original_data = pd.read_excel("data120.xlsx")
            labels = original_data['标注'].fillna(0).astype(int)
            
            # 分割（使用相同的随机种子）
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            # 标准化
            X_test_scaled = self.scaler.transform(X_test)
            self.X_test = pd.DataFrame(X_test_scaled, columns=features.columns)
            self.y_test = y_test.reset_index(drop=True)
            self.feature_names = list(features.columns)
            
            print(f"✅ 测试集: {len(self.X_test):,} 样本")
            print(f"   - 正常: {sum(self.y_test==0):,}")
            print(f"   - 水军: {sum(self.y_test==1):,}")
            
            return True
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return False
    
    def analyze_shap(self, num_samples=500):
        """SHAP分析（全局和局部）"""
        print("\n" + "="*70)
        print("【SHAP分析】全局特征重要性")
        print("="*70)
        print("原理: 基于博弈论的Shapley值，解释每个特征的贡献")
        
        # 采样数据（SHAP计算较慢）
        if len(self.X_test) > num_samples:
            print(f"\n采样 {num_samples} 个样本进行分析...")
            sample_indices = np.random.choice(len(self.X_test), num_samples, replace=False)
            X_sample = self.X_test.iloc[sample_indices]
            y_sample = self.y_test.iloc[sample_indices]
        else:
            X_sample = self.X_test
            y_sample = self.y_test
        
        print(f"计算SHAP值...")
        
        # 创建explainer
        explainer = shap.TreeExplainer(self.best_model)
        shap_values = explainer.shap_values(X_sample)
        
        # 对于二分类，取正类的SHAP值
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        print(f"✅ SHAP值计算完成")
        
        return explainer, shap_values, X_sample, y_sample
    
    def visualize_shap_summary(self, shap_values, X_sample, 
                              save_path='shap_summary.png'):
        """SHAP全局重要性可视化"""
        print("\n生成SHAP全局可视化...")
        
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        
        # 1. Feature Importance (bar plot)
        ax1 = axes[0]
        shap.summary_plot(shap_values, X_sample, 
                         plot_type="bar", 
                         show=False,
                         max_display=15)
        plt.sca(ax1)
        plt.title('SHAP特征重要性排名', fontsize=14, fontweight='bold', pad=20)
        
        # 2. Feature Effects (beeswarm plot)
        ax2 = axes[1]
        shap.summary_plot(shap_values, X_sample,
                         show=False,
                         max_display=15)
        plt.sca(ax2)
        plt.title('SHAP特征效应分布', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 保存: {save_path}")
        plt.close()
    
    def visualize_shap_waterfall(self, explainer, shap_values, X_sample,
                                y_sample, save_path='shap_waterfall.png'):
        """SHAP瀑布图（单个样本解释）"""
        print("\n生成SHAP瀑布图（单样本解释）...")
        
        # 找出几个有代表性的样本
        # 1. 真阳性（正确预测的水军）
        predictions = self.best_model.predict(X_sample)
        tp_indices = np.where((predictions == 1) & (y_sample == 1))[0]
        
        # 2. 假阳性（误判为水军）
        fp_indices = np.where((predictions == 1) & (y_sample == 0))[0]
        
        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        
        # 真阳性示例1
        if len(tp_indices) > 0:
            idx = tp_indices[0]
            ax = axes[0, 0]
            plt.sca(ax)
            
            shap_exp = shap.Explanation(
                values=shap_values[idx],
                base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[1],
                data=X_sample.iloc[idx].values,
                feature_names=self.feature_names
            )
            shap.plots.waterfall(shap_exp, show=False, max_display=10)
            ax.set_title('示例1: 真实水军（正确识别）', fontsize=12, fontweight='bold')
        
        # 真阳性示例2
        if len(tp_indices) > 1:
            idx = tp_indices[1]
            ax = axes[0, 1]
            plt.sca(ax)
            
            shap_exp = shap.Explanation(
                values=shap_values[idx],
                base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[1],
                data=X_sample.iloc[idx].values,
                feature_names=self.feature_names
            )
            shap.plots.waterfall(shap_exp, show=False, max_display=10)
            ax.set_title('示例2: 真实水军（正确识别）', fontsize=12, fontweight='bold')
        
        # 假阳性示例1
        if len(fp_indices) > 0:
            idx = fp_indices[0]
            ax = axes[1, 0]
            plt.sca(ax)
            
            shap_exp = shap.Explanation(
                values=shap_values[idx],
                base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[1],
                data=X_sample.iloc[idx].values,
                feature_names=self.feature_names
            )
            shap.plots.waterfall(shap_exp, show=False, max_display=10)
            ax.set_title('示例3: 正常用户（误判为水军）', fontsize=12, fontweight='bold')
        
        # 假阳性示例2
        if len(fp_indices) > 1:
            idx = fp_indices[1]
            ax = axes[1, 1]
            plt.sca(ax)
            
            shap_exp = shap.Explanation(
                values=shap_values[idx],
                base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[1],
                data=X_sample.iloc[idx].values,
                feature_names=self.feature_names
            )
            shap.plots.waterfall(shap_exp, show=False, max_display=10)
            ax.set_title('示例4: 正常用户（误判为水军）', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 保存: {save_path}")
        plt.close()
    
    def analyze_lime(self, num_samples=3):
        """LIME局部解释"""
        print("\n" + "="*70)
        print("【LIME分析】局部可解释性")
        print("="*70)
        print("原理: 在样本附近拟合简单模型，解释单个预测")
        
        # 创建LIME explainer
        explainer = lime_tabular.LimeTabularExplainer(
            self.X_test.values,
            feature_names=self.feature_names,
            class_names=['正常', '水军'],
            mode='classification',
            random_state=42
        )
        
        # 选择几个样本
        predictions = self.best_model.predict(self.X_test)
        
        # 找水军样本
        spam_indices = np.where(predictions == 1)[0]
        
        lime_explanations = []
        
        print(f"\n分析 {min(num_samples, len(spam_indices))} 个水军样本...")
        
        for i, idx in enumerate(spam_indices[:num_samples]):
            print(f"  样本 {i+1}...")
            exp = explainer.explain_instance(
                self.X_test.iloc[idx].values,
                self.best_model.predict_proba,
                num_features=10
            )
            lime_explanations.append(exp)
        
        print(f"✅ LIME分析完成")
        
        return explainer, lime_explanations
    
    def visualize_lime(self, lime_explanations, save_path='lime_explanations.png'):
        """可视化LIME解释"""
        print("\n生成LIME可视化...")
        
        n_samples = len(lime_explanations)
        fig, axes = plt.subplots(n_samples, 1, figsize=(12, 5*n_samples))
        
        if n_samples == 1:
            axes = [axes]
        
        for i, exp in enumerate(lime_explanations):
            ax = axes[i]
            
            # 获取特征贡献
            exp_list = exp.as_list()
            features = [f[0] for f in exp_list]
            weights = [f[1] for f in exp_list]
            
            # 颜色编码
            colors = ['green' if w < 0 else 'red' for w in weights]
            
            ax.barh(range(len(weights)), weights, color=colors, alpha=0.7)
            ax.set_yticks(range(len(features)))
            ax.set_yticklabels(features, fontsize=9)
            ax.set_xlabel('特征贡献值', fontsize=11)
            ax.set_title(f'样本 {i+1} 的LIME解释 (红色:促进水军判定, 绿色:抑制)', 
                        fontsize=12, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 保存: {save_path}")
        plt.close()
    
    def generate_feature_importance_report(self, shap_values, X_sample):
        """生成特征重要性报告"""
        print("\n" + "="*70)
        print("【特征重要性报告】")
        print("="*70)
        
        # 计算平均绝对SHAP值
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        importance_df = pd.DataFrame({
            'Feature': self.feature_names,
            'Importance': mean_abs_shap
        }).sort_values('Importance', ascending=False)
        
        print("\nTop 15 最重要特征:")
        print(importance_df.head(15).to_string(index=False))
        
        # 保存
        importance_df.to_csv('feature_importance_shap.csv', index=False)
        print(f"\n✅ 完整报告已保存: feature_importance_shap.csv")
        
        return importance_df
    
    def generate_detection_report(self):
        """生成综合检测报告"""
        print("\n" + "="*70)
        print("【生成综合检测报告】")
        print("="*70)
        
        # 预测
        y_pred = self.best_model.predict(self.X_test)
        y_pred_proba = self.best_model.predict_proba(self.X_test)[:, 1]
        
        # 加载原始数据
        original_data = pd.read_excel("data120.xlsx")
        from sklearn.model_selection import train_test_split
        _, test_data, _, _ = train_test_split(
            original_data, original_data['标注'].fillna(0), 
            test_size=0.2, random_state=42, 
            stratify=original_data['标注'].fillna(0)
        )
        
        # 创建报告
        report_df = test_data.copy()
        report_df = report_df.reset_index(drop=True)
        report_df['预测标签'] = y_pred
        report_df['水军概率'] = y_pred_proba
        report_df['置信度'] = np.abs(y_pred_proba - 0.5) * 2
        
        # 风险等级
        def risk_level(prob):
            if prob >= 0.8:
                return '高风险'
            elif prob >= 0.6:
                return '中风险'
            elif prob >= 0.4:
                return '低风险'
            else:
                return '正常'
        
        report_df['风险等级'] = report_df['水军概率'].apply(risk_level)
        
        # 保存
        report_df.to_csv('water_army_detection_report.csv', index=False, encoding='utf-8-sig')
        
        print("\n报告统计:")
        print(f"  总评论数: {len(report_df):,}")
        print(f"  预测水军: {sum(y_pred==1):,}")
        print(f"  预测正常: {sum(y_pred==0):,}")
        
        print(f"\n风险等级分布:")
        for level in ['高风险', '中风险', '低风险', '正常']:
            count = sum(report_df['风险等级'] == level)
            pct = count / len(report_df) * 100
            print(f"  {level}: {count:,} ({pct:.1f}%)")
        
        print(f"\n✅ 完整报告已保存: water_army_detection_report.csv")
        
        # 高风险样本
        high_risk = report_df[report_df['风险等级'] == '高风险']
        if len(high_risk) > 0:
            print(f"\n高风险样本示例（前5条）:")
            # 选择存在的列
            display_cols = ['水军概率', '风险等级']
            if '评论内容' in report_df.columns:
                display_cols.insert(0, '评论内容')
            elif 'content' in report_df.columns:
                display_cols.insert(0, 'content')
            print(high_risk[display_cols].head().to_string(index=False))
        
        return report_df
    
    def create_summary_visualization(self, report_df, save_path='detection_summary.png'):
        """创建综合可视化"""
        print("\n生成检测总结可视化...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 风险等级分布
        ax = axes[0, 0]
        risk_counts = report_df['风险等级'].value_counts()
        colors = {'高风险': 'red', '中风险': 'orange', '低风险': 'yellow', '正常': 'green'}
        risk_colors = [colors.get(r, 'gray') for r in risk_counts.index]
        
        ax.pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%',
              colors=risk_colors, startangle=90)
        ax.set_title('风险等级分布', fontsize=14, fontweight='bold')
        
        # 2. 水军概率分布
        ax = axes[0, 1]
        ax.hist(report_df[report_df['预测标签']==0]['水军概率'], 
               bins=50, alpha=0.6, label='正常用户', color='green')
        ax.hist(report_df[report_df['预测标签']==1]['水军概率'], 
               bins=50, alpha=0.6, label='水军', color='red')
        ax.axvline(x=0.5, color='black', linestyle='--', label='阈值')
        ax.set_xlabel('水军概率')
        ax.set_ylabel('数量')
        ax.set_title('水军概率分布', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. 置信度分布
        ax = axes[1, 0]
        ax.boxplot([report_df[report_df['预测标签']==0]['置信度'],
                   report_df[report_df['预测标签']==1]['置信度']],
                  labels=['正常', '水军'])
        ax.set_ylabel('预测置信度')
        ax.set_title('预测置信度分布', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. 混淆矩阵
        ax = axes[1, 1]
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(report_df['标注'].fillna(0), report_df['预测标签'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                   xticklabels=['正常', '水军'],
                   yticklabels=['正常', '水军'])
        ax.set_title('混淆矩阵', fontsize=14, fontweight='bold')
        ax.set_ylabel('真实标签')
        ax.set_xlabel('预测标签')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 保存: {save_path}")
        plt.close()


def main():
    """主函数"""
    print("\n" + "🔬"*35)
    print("\n" + " "*12 + "步骤5：可解释性分析与检测报告")
    print(" "*10 + "SHAP + LIME 模型解释 + 生成详细报告")
    print("\n" + "🔬"*35)
    
    # 1. 初始化分析器
    print("\n【阶段1】初始化分析器")
    print("-"*70)
    
    analyzer = ExplainabilityAnalyzer(model_path='models_improved')
    
    # 2. 加载模型
    if not analyzer.load_models():
        print("\n❌ 无法加载模型，请先运行 step4")
        return
    
    # 3. 加载测试数据
    if not analyzer.load_test_data():
        print("\n❌ 无法加载数据")
        return
    
    # 4. SHAP分析
    print("\n【阶段2】SHAP全局分析")
    print("-"*70)
    
    explainer, shap_values, X_sample, y_sample = analyzer.analyze_shap(num_samples=500)
    
    # 5. SHAP可视化
    print("\n【阶段3】SHAP可视化")
    print("-"*70)
    
    analyzer.visualize_shap_summary(shap_values, X_sample, 'shap_summary.png')
    analyzer.visualize_shap_waterfall(explainer, shap_values, X_sample, y_sample, 
                                     'shap_waterfall.png')
    
    # 6. 特征重要性报告
    print("\n【阶段4】特征重要性分析")
    print("-"*70)
    
    importance_df = analyzer.generate_feature_importance_report(shap_values, X_sample)
    
    # 7. LIME分析
    print("\n【阶段5】LIME局部解释")
    print("-"*70)
    
    lime_explainer, lime_explanations = analyzer.analyze_lime(num_samples=3)
    analyzer.visualize_lime(lime_explanations, 'lime_explanations.png')
    
    # 8. 生成检测报告
    print("\n【阶段6】生成综合检测报告")
    print("-"*70)
    
    report_df = analyzer.generate_detection_report()
    
    # 9. 综合可视化
    print("\n【阶段7】生成总结可视化")
    print("-"*70)
    
    analyzer.create_summary_visualization(report_df, 'detection_summary.png')
    
    # 10. 总结
    print("\n" + "="*70)
    print("✅ 可解释性分析完成！")
    print("="*70)
    
    print("\n📊 生成的文件:")
    print("  【SHAP分析】")
    print("    • shap_summary.png - SHAP全局特征重要性")
    print("    • shap_waterfall.png - SHAP瀑布图（单样本解释）")
    print("    • feature_importance_shap.csv - 特征重要性表")
    
    print("\n  【LIME分析】")
    print("    • lime_explanations.png - LIME局部解释")
    
    print("\n  【检测报告】")
    print("    • water_army_detection_report.csv - 完整检测报告")
    print("    • detection_summary.png - 检测总结可视化")
    
    print("\n📈 关键发现:")
    top_features = importance_df.head(5)
    print("  最重要的5个特征:")
    for i, row in top_features.iterrows():
        print(f"    {i+1}. {row['Feature']}: {row['Importance']:.4f}")
    
    print("\n🎉 所有分析完成！")
    print("="*70)


if __name__ == "__main__":
    main()