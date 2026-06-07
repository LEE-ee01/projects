import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from tqdm import tqdm
import random
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
import time
import os
import math
import matplotlib.pyplot as plt


# 全局配置与工具
SEED = 2024
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f">>> Using Device: {DEVICE}")

# 数据预处理模块
def load_and_preprocess_data(root_path='./'):
    print(">>> 1. Loading Data...")
    
    # Users
    u_cols = ['user_id', 'gender', 'age', 'occupation', 'zip_code']
    users = pd.read_csv(f'{root_path}users.dat', sep='::', header=None, names=u_cols, engine='python', encoding='latin-1')
    users = users.drop('zip_code', axis=1)
    users['gender'] = LabelEncoder().fit_transform(users['gender'])
    users['age'] = LabelEncoder().fit_transform(users['age'])
    
    # Movies
    m_cols = ['movie_id', 'title', 'genres']
    movies = pd.read_csv(f'{root_path}movies.dat', sep='::', header=None, names=m_cols, engine='python', encoding='latin-1')
    movies['genres'] = movies['genres'].apply(lambda x: x.split('|'))
    mlb = MultiLabelBinarizer()
    genres_matrix = mlb.fit_transform(movies['genres'])
    
    # Ratings
    r_cols = ['user_id', 'movie_id', 'rating', 'timestamp']
    ratings = pd.read_csv(f'{root_path}ratings.dat', sep='::', header=None, names=r_cols, engine='python', encoding='latin-1')

    print(">>> 2. Re-indexing IDs...")
    user2idx = {uid: i for i, uid in enumerate(users['user_id'].unique())}
    movie2idx = {mid: i for i, mid in enumerate(movies['movie_id'].unique())}
    
    users['user_idx'] = users['user_id'].map(user2idx)
    movies['movie_idx'] = movies['movie_id'].map(movie2idx)
    ratings['user_idx'] = ratings['user_id'].map(user2idx)
    ratings['movie_idx'] = ratings['movie_id'].map(movie2idx)
    
    ratings = ratings.dropna(subset=['user_idx', 'movie_idx'])
    ratings[['user_idx', 'movie_idx']] = ratings[['user_idx', 'movie_idx']].astype(int)

    num_users = len(user2idx)
    num_items = len(movie2idx)
    
    # 计算物品新颖度 
    item_counts = ratings['movie_idx'].value_counts().to_dict()
    total_interactions = len(ratings)
    item_novelty_score = {}
    for iid in range(num_items):
        count = item_counts.get(iid, 1)
        prob = count / total_interactions
        item_novelty_score[iid] = -math.log2(prob)

    print(">>> 3. Splitting Data (Leave-One-Out)...")
    ratings = ratings.sort_values(by=['user_idx', 'timestamp'])
    
    train_data, val_data, test_data = [], [], []
    
    for _, group in tqdm(ratings.groupby('user_idx')):
        interacts = group[['user_idx', 'movie_idx']].values.tolist()
        if len(interacts) < 3:
            train_data.extend(interacts)
            continue
        test_data.append(interacts[-1])
        val_data.append(interacts[-2])
        train_data.extend(interacts[:-2])

    train_df = pd.DataFrame(train_data, columns=['user_idx', 'movie_idx'])
    val_df = pd.DataFrame(val_data, columns=['user_idx', 'movie_idx'])
    test_df = pd.DataFrame(test_data, columns=['user_idx', 'movie_idx'])
    
    data_bundle = {
        'train_df': train_df, 'val_df': val_df, 'test_df': test_df,
        'user_features': users, 'item_features': movies,
        'genres_matrix': genres_matrix,
        'num_users': num_users, 'num_items': num_items,
        'item_novelty_score': item_novelty_score 
    }
    
    return data_bundle


# Dataset 类

class BPRDataset(Dataset):
    def __init__(self, df, num_items, is_training=True):
        self.users = torch.tensor(df['user_idx'].values, dtype=torch.long)
        self.items = torch.tensor(df['movie_idx'].values, dtype=torch.long)
        self.num_items = num_items
        self.is_training = is_training
        
        if is_training:
            self.train_mat = df.groupby('user_idx')['movie_idx'].apply(set).to_dict()

    def __len__(self):
        return len(self.users)

    def __getitem__(self, idx):
        user = self.users[idx]
        pos_item = self.items[idx]
        
        if not self.is_training:
            return user, pos_item
            
        neg_item = np.random.randint(0, self.num_items)
        while neg_item in self.train_mat[user.item()]:
            neg_item = np.random.randint(0, self.num_items)
            
        return user, pos_item, torch.tensor(neg_item, dtype=torch.long)

def get_dataloaders(data_bundle, batch_size=2048):
    train_df = data_bundle['train_df']
    num_items = data_bundle['num_items']
    train_dataset = BPRDataset(train_df, num_items, is_training=True)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    return train_loader


# 模型定义 (BPR-MF)

class BPRModel(nn.Module):
    def __init__(self, num_users, num_items, embed_dim=64):
        super(BPRModel, self).__init__()
        self.user_embedding = nn.Embedding(num_users, embed_dim)
        self.item_embedding = nn.Embedding(num_items, embed_dim)
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.item_embedding.weight, std=0.01)

    def forward(self, user_indices, item_indices):
        user_vec = self.user_embedding(user_indices)
        item_vec = self.item_embedding(item_indices)
        return torch.mul(user_vec, item_vec).sum(dim=1)

    def calculate_loss(self, users, pos_items, neg_items):
        pos_scores = self.forward(users, pos_items)
        neg_scores = self.forward(users, neg_items)
        loss = -torch.mean(torch.nn.functional.logsigmoid(pos_scores - neg_scores))
        reg_loss = 0.5 * (self.user_embedding(users).norm(2).pow(2) + 
                          self.item_embedding(pos_items).norm(2).pow(2) + 
                          self.item_embedding(neg_items).norm(2).pow(2)) / float(len(users))
        return loss, reg_loss


# 训练函数 

def train_model(data_bundle, train_loader, epochs=20, lr=0.001, save_path="bpr_model_best.pth"):
    print(f">>> Initialize Model on {DEVICE}...")
    num_users = data_bundle['num_users']
    num_items = data_bundle['num_items']
    
    model = BPRModel(num_users, num_items, embed_dim=64).to(DEVICE)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    loss_history = []
    print(">>> Start Training...")
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for batch_idx, (users, pos_items, neg_items) in enumerate(train_loader):
            users, pos_items, neg_items = users.to(DEVICE), pos_items.to(DEVICE), neg_items.to(DEVICE)
            
            optimizer.zero_grad()
            loss, reg_loss = model.calculate_loss(users, pos_items, neg_items)
            final_loss = loss + 1e-4 * reg_loss
            final_loss.backward()
            optimizer.step()
            total_loss += final_loss.item()
            
        avg_loss = total_loss / len(train_loader)
        loss_history.append(avg_loss)
        print(f"Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f}")
        
    print(">>> Training Finished!")
    torch.save(model.state_dict(), save_path)
    return model, loss_history


# 评估函数 
def evaluate_model(model, data_bundle, k=10):
    print(f"\n>>> [Evaluation] Calculating Metrics @ {k}...")
    model.eval()
    
    test_df = data_bundle['test_df']
    num_items = data_bundle['num_items']
    train_df = data_bundle['train_df']
    user_history = train_df.groupby('user_idx')['movie_idx'].apply(set).to_dict()
    item_novelty_score = data_bundle['item_novelty_score']
    

    metrics = {'Recall@10': [], 'nDCG@10': [], 'Novelty@10': [], 'AUC': []}
    recommended_items_set = set()
    
    test_users = test_df['user_idx'].values
    test_items = test_df['movie_idx'].values
    
    with torch.no_grad():
        for i in tqdm(range(len(test_users))):
            u = test_users[i]
            pos_item = test_items[i]
            
            neg_candidates = []
            while len(neg_candidates) < 99:
                rand_id = np.random.randint(0, num_items)
                if rand_id not in user_history.get(u, set()) and rand_id != pos_item:
                    neg_candidates.append(rand_id)
            
            candidates = [pos_item] + neg_candidates
            
            u_tensor = torch.tensor([u] * 100).to(DEVICE)
            i_tensor = torch.tensor(candidates).to(DEVICE)
            
            scores = model(u_tensor, i_tensor).cpu().numpy()


            pos_score = scores[0]
            neg_scores = scores[1:]
            # 计算正样本得分大于负样本得分的比例
            auc = np.mean((pos_score > neg_scores).astype(float))
            metrics['AUC'].append(auc)

            rank_indices = np.argsort(scores)[::-1]

            top_k_indices = rank_indices[:k]
            top_k_items = [candidates[idx] for idx in top_k_indices]
            
            for item in top_k_items:
                recommended_items_set.add(item)
            
            nov_score = np.mean([item_novelty_score.get(item, 0) for item in top_k_items])
            metrics['Novelty@10'].append(nov_score)
            
            rank_position = np.where(rank_indices == 0)[0][0]
            if rank_position < k:
                metrics['Recall@10'].append(1.0)
                metrics['nDCG@10'].append(1.0 / np.log2(rank_position + 2))
            else:
                metrics['Recall@10'].append(0.0)
                metrics['nDCG@10'].append(0.0)

    res = {key: np.mean(val) for key, val in metrics.items()}
    res['Coverage@10'] = len(recommended_items_set) / num_items
    
    print("\n>>> Evaluation Results:")
    for k, v in res.items():
        print(f"    {k}: {v:.4f}")
        
    return res


# Visualization

def plot_results(metrics, loss_history):
    # 设置风格
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 图 1: Training Loss
    ax1.plot(loss_history, label='Training Loss', color='#1f77b4', linewidth=2.5)
    ax1.set_title('BPR-MF Training Loss Convergence', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Epochs', fontsize=12)
    ax1.set_ylabel('BPR Loss', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=12)
    
    # 图 2: Metrics (双坐标轴优化) 

    left_metrics = ['Recall@10', 'nDCG@10', 'Coverage@10', 'AUC']
    right_metrics = ['Novelty@10']
    
    labels = left_metrics + right_metrics
    data_left = [metrics[k] for k in left_metrics]
    data_right = [metrics[k] for k in right_metrics]
    
    x = np.arange(len(labels))
    
    # 绘制左轴 (0-1 Scale)
    ax2_left = ax2

    colors = ['#2ca02c', '#ff7f0e', '#d62728', '#17becf'] 
    bars1 = ax2_left.bar(x[:4], data_left, color=colors, alpha=0.9, label='Accuracy/Coverage')
    ax2_left.set_ylabel('Score (0-1)', fontsize=12, fontweight='bold')
    ax2_left.set_ylim(0, 1.1) 
    
    # 绘制右轴 (Novelty Scale)
    ax2_right = ax2.twinx()
    bars2 = ax2_right.bar(x[4:], data_right, color=['#9467bd'], alpha=0.9, label='Novelty')
    ax2_right.set_ylabel('Novelty Score (>1)', fontsize=12, fontweight='bold', rotation=270, labelpad=15)
    ax2_right.set_ylim(0, 14) 
    
    # 设置 X 轴标签
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=11, fontweight='bold')
    ax2.set_title('BPR-MF Evaluation Metrics', fontsize=14, fontweight='bold')
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax2_left.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                      f'{height:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    for bar in bars2:
        height = bar.get_height()
        ax2_right.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                       f'{height:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('bpr_report_optimized.png', dpi=300)
    print(">>> Visualization saved to 'bpr_report_optimized.png'")


if __name__ == "__main__":
    data = load_and_preprocess_data()
    train_loader = get_dataloaders(data, batch_size=2048)
    
    # Train
    model, loss_hist = train_model(data, train_loader, epochs=500)
    
    # Evaluate
    print("\n>>> Loading best model for testing...")
    model.load_state_dict(torch.load("bpr_model_best.pth"))
    metrics = evaluate_model(model, data, k=10)
    
    # Plot
    plot_results(metrics, loss_hist)