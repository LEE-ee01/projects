import matplotlib.pyplot as plt
import numpy as np


# 横轴：Transformer 层数
layers = [2, 3, 4, 5]

# 纵轴数据
recall = [0.9733, 0.9801, 0.9680, 0.9758]
ndcg = [0.7934, 0.8108, 0.7978, 0.7893]
auc = [0.9857, 0.9882, 0.9852, 0.9863]       
novelty = [12.4501, 12.4778, 12.4560, 12.4210]
coverage = [0.5057, 0.5232, 0.5445, 0.5391]

# 绘图风格
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except:
    plt.style.use('ggplot')

fig, ax1 = plt.subplots(figsize=(10, 6))

# 左侧坐标轴 (用于 Recall, nDCG, AUC, Coverage) 
ax1.set_xlabel('Number of Transformer Blocks', fontsize=12, fontweight='bold')
ax1.set_ylabel('Recall / nDCG / AUC / Coverage', fontsize=12, fontweight='bold')

# 绘制左轴折线
# Recall 
ax1.plot(layers, recall, label='Recall@10', color='#2ca02c', marker='o', linewidth=2.5)
# nDCG 
ax1.plot(layers, ndcg, label='nDCG@10', color='#ff7f0e', marker='s', linewidth=2.5)
# AUC 
ax1.plot(layers, auc, label='AUC', color='#17becf', marker='*', markersize=10, linewidth=2.5)
# Coverage
ax1.plot(layers, coverage, label='Coverage@10', color='#d62728', marker='^', linewidth=2.5)

# 设置左轴范围
ax1.set_ylim(0.4, 1.05)
ax1.set_xticks(layers)
ax1.tick_params(axis='y', labelsize=10)

# 右侧坐标轴 (专门用于 Novelty)
ax2 = ax1.twinx()
ax2.set_ylabel('Novelty@10', fontsize=12, fontweight='bold', rotation=270, labelpad=20)

# 绘制 Novelty
ax2.plot(layers, novelty, label='Novelty@10', color='#9467bd', marker='D', linewidth=2.5, linestyle='--')

# 设置右轴范围
ax2.set_ylim(12.3, 12.6)
ax2.tick_params(axis='y', labelsize=10)

plt.title('Hyperparameter Sensitivity: Number of Transformer Layers', fontsize=14, fontweight='bold', pad=15)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=10, frameon=True, shadow=True)

plt.tight_layout()
plt.savefig('layers_ablation_with_auc.png', dpi=300)
print(">>> 图表已保存为 'layers_ablation_with_auc.png'")
plt.show()