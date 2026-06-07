import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer, MinMaxScaler
from tqdm import tqdm
import random
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import time
import os
import matplotlib.pyplot as plt
import math

# 全局配置与工具
SEED = 2024
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f">>> Using Device: {DEVICE}")


# 深度特征工程与数据加载
def load_and_enrich_data(root_path='./'):
    print(">>> [Data Layer] Loading and Feature Engineering...")
    
    # Load Raw Data 
    users = pd.read_csv(f'{root_path}users.dat', sep='::', header=None, names=['user_id', 'gender', 'age', 'occupation', 'zip'], engine='python', encoding='latin-1')
    movies = pd.read_csv(f'{root_path}movies.dat', sep='::', header=None, names=['movie_id', 'title', 'genres'], engine='python', encoding='latin-1')
    ratings = pd.read_csv(f'{root_path}ratings.dat', sep='::', header=None, names=['user_id', 'movie_id', 'rating', 'timestamp'], engine='python', encoding='latin-1')
    
    # Feature Engineering: User 
    le_gender = LabelEncoder()
    users['gender'] = le_gender.fit_transform(users['gender'])
    users['age'] = LabelEncoder().fit_transform(users['age']) 
    users['occupation'] = LabelEncoder().fit_transform(users['occupation'])
    
    # Feature Engineering: Item 
    movies['genres'] = movies['genres'].apply(lambda x: x.split('|'))
    mlb = MultiLabelBinarizer()
    genres_matrix = mlb.fit_transform(movies['genres']) 
    
    # Feature Engineering: Interaction (Time Decay)
    scaler = MinMaxScaler()
    ratings['time_score'] = scaler.fit_transform(ratings['timestamp'].values.reshape(-1, 1))
    
    # ID Remapping 
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


    item_counts = ratings['movie_idx'].value_counts().to_dict()
    total_interactions = len(ratings)

    item_novelty_score = {}

    for iid in range(num_items):
        count = item_counts.get(iid, 1) # 平滑处理，最少为1
        prob = count / total_interactions
        item_novelty_score[iid] = -math.log2(prob)
    
    # Data Splitting (Leave-One-Out) 
    print(">>> [Data Layer] Splitting Data (Leave-One-Out)...")
    ratings = ratings.sort_values(by=['user_idx', 'timestamp'])
    
    train_data, val_data, test_data = [], [], []
    
    for u in tqdm(ratings['user_idx'].unique()):
        u_records = ratings[ratings['user_idx'] == u]
        if len(u_records) < 3:
            train_data.append(u_records)
            continue
            
        test_data.append(u_records.iloc[[-1]])
        val_data.append(u_records.iloc[[-2]])
        train_data.append(u_records.iloc[:-2])
        
    train_df = pd.concat(train_data)
    val_df = pd.concat(val_data)
    test_df = pd.concat(test_data)
    
    print(f"    Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    return {
        'train_df': train_df, 'val_df': val_df, 'test_df': test_df,
        'users': users, 'movies': movies, 'genres_matrix': genres_matrix,
        'num_users': num_users, 'num_items': num_items,
        'item_novelty_score': item_novelty_score 
    }

# Dataset & Loader 
class RecDataset(Dataset):
    def __init__(self, df):
        self.users = torch.tensor(df['user_idx'].values, dtype=torch.long)
        self.items = torch.tensor(df['movie_idx'].values, dtype=torch.long)
        
        rating_norm = torch.tensor(df['rating'].values / 5.0, dtype=torch.float)
        time_score = torch.tensor(df['time_score'].values, dtype=torch.float)
        
        self.weights = rating_norm * (1.0 + time_score)

    def __len__(self):
        return len(self.users)

    def __getitem__(self, idx):
        return self.users[idx], self.items[idx], self.weights[idx]

def get_dataloader(df, batch_size=2048):
    return DataLoader(RecDataset(df), batch_size=batch_size, shuffle=True, num_workers=0)

# Model
class HybridMF(nn.Module):
    def __init__(self, num_users, num_items, data_bundle, embed_dim=64):
        super(HybridMF, self).__init__()
        
        # ID Embeddings 
        self.user_emb = nn.Embedding(num_users, embed_dim)
        self.item_emb = nn.Embedding(num_items, embed_dim)
        
        # Side Info Embeddings 
        self.gender_emb = nn.Embedding(2, embed_dim)
        self.age_emb = nn.Embedding(7, embed_dim)
        
        # Genre 处理
        genres_matrix = torch.tensor(data_bundle['genres_matrix'], dtype=torch.float, device=DEVICE)
        num_genres = genres_matrix.shape[1]
        
        # 建立映射表
        self.genre_mapping = torch.zeros((num_items, num_genres), device=DEVICE)
        raw_movies = data_bundle['movies']
        mid_to_row = {row['movie_idx']: i for i, row in raw_movies.iterrows() if not pd.isna(row['movie_idx'])}
        valid_indices = sorted(mid_to_row.keys())
        for idx in valid_indices:
            self.genre_mapping[idx] = genres_matrix[mid_to_row[idx]]
            
        self.genre_trans = nn.Linear(num_genres, embed_dim)
        
        # Side Info 的辅助处理
        users_sorted = data_bundle['users'].sort_values('user_idx')
        self.user_genders = torch.tensor(users_sorted['gender'].values, device=DEVICE)
        self.user_ages = torch.tensor(users_sorted['age'].values, device=DEVICE)

        self.dropout = nn.Dropout(0.1)
        self.layernorm = nn.LayerNorm(embed_dim)
        
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Embedding): nn.init.xavier_normal_(m.weight)
            elif isinstance(m, nn.Linear): nn.init.kaiming_normal_(m.weight)

    def forward(self, u_idx, i_idx):
        # User Feature Fusion
        u_id = self.user_emb(u_idx)
        u_side = self.gender_emb(self.user_genders[u_idx]) + \
                 self.age_emb(self.user_ages[u_idx])
        
        # 融合策略：ID + SideInfo (类似 ResNet)
        # LayerNorm 保证数值稳定，防止梯度爆炸
        u_final = self.layernorm(u_id + self.dropout(u_side))
        
        # Item Feature Fusion
        i_id = self.item_emb(i_idx)
        i_genre_raw = self.genre_mapping[i_idx]
        i_side = torch.tanh(self.genre_trans(i_genre_raw))
        
        i_final = self.layernorm(i_id + self.dropout(i_side))
        
        # Dot Product
        return torch.mul(u_final, i_final).sum(dim=1)


# Training 
def train_model(model, data_bundle, epochs=20, lr=1e-3, save_path="hybrid_model_best.pth"):
    print(f">>> [Training] Start training for {epochs} epochs...")
    
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    train_loader = get_dataloader(data_bundle['train_df'])
    
    num_users, num_items = data_bundle['num_users'], data_bundle['num_items']
    train_df = data_bundle['train_df']
    

    # 使用 np.vstack 先堆叠，再转 Tensor
    indices = np.vstack((train_df['user_idx'].values, train_df['movie_idx'].values))
    i = torch.LongTensor(indices)
    v = torch.ones(len(train_df))
    adj_mask = torch.sparse_coo_tensor(i, v, (num_users, num_items)).to_dense().bool().to(DEVICE)

    loss_history = []
    best_recall = 0.0
    best_epoch = -1
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for users, pos_items, weights in train_loader:
            users, pos_items, weights = users.to(DEVICE), pos_items.to(DEVICE), weights.to(DEVICE)
            
            # 1 vs 5 采样
            num_neg = 10
            users_rep = users.repeat_interleave(num_neg)
            pos_items_rep = pos_items.repeat_interleave(num_neg)
            weights_rep = weights.repeat_interleave(num_neg)
            
            neg_items = torch.randint(0, num_items, (users_rep.size(0),), device=DEVICE)
            collisions = adj_mask[users_rep, neg_items]
            if collisions.any():
                neg_items[collisions] = torch.randint(0, num_items, (collisions.sum(),), device=DEVICE)
                
            pos_scores = model(users_rep, pos_items_rep)
            neg_scores = model(users_rep, neg_items)
            
            loss = -torch.mean(weights_rep * torch.nn.functional.logsigmoid(pos_scores - neg_scores))
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_loss = total_loss / len(train_loader)
        loss_history.append(avg_loss)
        

        print(f"Epoch {epoch+1}/{epochs} | Loss: {avg_loss:.4f}", end="")

        val_metrics = evaluate(model, data_bundle, k=10, quiet=True) 
        val_recall = val_metrics['Recall@10']
        
        print(f" | Val Recall@10: {val_recall:.4f}", end="")
        
        if val_recall > best_recall:
            best_recall = val_recall
            best_epoch = epoch + 1
            torch.save(model.state_dict(), save_path)
            print(" -> Best! Saved.")
        else:
            print("") 
            
    print(f"\n>>> Training Finished. Best Recall@10: {best_recall:.4f} at Epoch {best_epoch}")
    return loss_history


# Evaluation Engine 
def evaluate(model, data_bundle, k=10, quiet=False):
    if not quiet:
        print(f">>> [Evaluation] Calculating Metrics @ {k}...")
    model.eval()
    test_df = data_bundle['test_df']
    num_items = data_bundle['num_items']
    train_df = data_bundle['train_df']
    
    # 查找表
    user_history = train_df.groupby('user_idx')['movie_idx'].apply(set).to_dict()
    item_novelty_score = data_bundle['item_novelty_score']

    metrics = {'Recall@10': [], 'nDCG@10': [], 'Novelty@10': [], 'AUC': []}
    
    recommended_items_set = set()
    
    test_users = test_df['user_idx'].values
    test_items = test_df['movie_idx'].values
    
    iter_wrapper = tqdm(range(len(test_users))) if not quiet else range(len(test_users))
    
    with torch.no_grad():
        for i in iter_wrapper:
            u = test_users[i]
            pos_item = test_items[i]
            
            candidates = [pos_item]
            while len(candidates) < 100:
                neg = np.random.randint(0, num_items)
                if neg not in user_history.get(u, set()) and neg != pos_item:
                    candidates.append(neg)
            
            candidates_tensor = torch.tensor(candidates).to(DEVICE)
            user_tensor = torch.tensor([u] * 100).to(DEVICE)
            
            scores = model(user_tensor, candidates_tensor).cpu().numpy()
            
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

            # 计算 Recall / nDCG
            if 0 in top_k_indices: # 0 is index of pos_item
                metrics['Recall@10'].append(1.0)
                rank = np.where(top_k_indices == 0)[0][0]
                metrics['nDCG@10'].append(1.0 / np.log2(rank + 2))
            else:
                metrics['Recall@10'].append(0.0)
                metrics['nDCG@10'].append(0.0)

    res = {k: np.mean(v) for k, v in metrics.items()}
    res['Coverage@10'] = len(recommended_items_set) / num_items
    
    return res


# Visualization
def plot_results(metrics_final, loss_history):
    # 设置风格
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 图 1: Training Loss 
    ax1.plot(loss_history, label='HybridMF Training Loss', color='#1f77b4', linewidth=2.5)
    ax1.set_title('HybridMF Training Loss Convergence', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Epochs', fontsize=12)
    ax1.set_ylabel('Weighted BPR Loss', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=12)
    
    # 图 2: Metrics (双坐标轴)
    left_metrics = ['Recall@10', 'nDCG@10', 'Coverage@10', 'AUC']
    right_metrics = ['Novelty@10']
    
    labels = left_metrics + right_metrics
    data_left = [metrics_final[k] for k in left_metrics]
    data_right = [metrics_final[k] for k in right_metrics]
    
    x = np.arange(len(labels))
    
    # 左轴 (0-1 Scale)
    ax2_left = ax2
    colors = ['#2ca02c', '#ff7f0e', '#d62728', '#17becf']
    bars1 = ax2_left.bar(x[:4], data_left, color=colors, alpha=0.9, label='Accuracy/Coverage')
    ax2_left.set_ylabel('Score (0-1)', fontsize=12, fontweight='bold')
    ax2_left.set_ylim(0, 1.1) 
    
    # 右轴 (Novelty Scale)
    ax2_right = ax2.twinx()
    bars2 = ax2_right.bar(x[4:], data_right, color=['#9467bd'], alpha=0.9, label='Novelty')
    ax2_right.set_ylabel('Novelty Score (>1)', fontsize=12, fontweight='bold', rotation=270, labelpad=15)
    ax2_right.set_ylim(0, 15)
    
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=11, fontweight='bold', rotation=15)
    ax2.set_title('HybridMF Evaluation Metrics', fontsize=14, fontweight='bold')
    
    # 添加数值
    for bar in bars1:
        height = bar.get_height()
        ax2_left.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                      f'{height:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    for bar in bars2:
        height = bar.get_height()
        ax2_right.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                       f'{height:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('hybridmf_report_optimized.png', dpi=300)
    print(">>> Visualization saved to 'hybridmf_report_optimized.png'")


if __name__ == "__main__":
    # Data
    data = load_and_enrich_data()
    
    # Model
    model = HybridMF(data['num_users'], data['num_items'], data, embed_dim=64).to(DEVICE)

    # Train
    loss_hist = train_model(model, data, epochs=500, lr=0.0005) 
    
    # Evaluation
    print("\n>>> Loading Best Model for Final Test...")
    model.load_state_dict(torch.load("hybrid_model_best.pth"))
    
    final_metrics = evaluate(model, data, k=10)
    
    print("\n>>> Final Report (Aligned with SASRec):")
    for k, v in final_metrics.items():
        print(f"{k}: {v:.4f}")
    
    # Visualize
    plot_results(final_metrics, loss_hist)