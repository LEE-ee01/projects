import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import time
import random
import sys
import matplotlib.pyplot as plt
import math


# 全局配置
SEED = 2024
MAX_LEN = 200        # 序列最大长度
BATCH_SIZE = 128
LR = 0.001
EPOCHS = 500         
EMBED_DIM = 64       # 隐向量维度
NUM_BLOCKS = 5       # Transformer 层数
NUM_HEADS = 1        # 多头注意力头数
DROPOUT_RATE = 0.1
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 固定随机种子
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

print(f">>> Using Device: {DEVICE}")


# 数据预处理 (序列化)

def data_partition(fname):
    print(f">>> Loading {fname}...")
    df = pd.read_csv(fname, sep='::', header=None, names=['user_id', 'movie_id', 'rating', 'timestamp'],
                     engine='python', encoding='latin-1')
    
    # ID 重新映射
    user_ids = df['user_id'].unique()
    item_ids = df['movie_id'].unique()
    user2idx = {uid: i+1 for i, uid in enumerate(user_ids)} 
    item2idx = {mid: i+1 for i, mid in enumerate(item_ids)}
    df['user_idx'] = df['user_id'].map(user2idx)
    df['movie_idx'] = df['movie_id'].map(item2idx)
    
    num_users = len(user2idx)
    num_items = len(item2idx)

    item_counts = df['movie_idx'].value_counts().to_dict()
    total_interactions = len(df)

    item_novelty_score = {}
    for iid in range(1, num_items + 1):
        count = item_counts.get(iid, 1) # 平滑处理，最少为1
        prob = count / total_interactions
        item_novelty_score[iid] = -math.log2(prob)

    # 构建序列
    User = df.groupby('user_idx')['movie_idx'].apply(list).to_dict()
    
    # 划分数据集
    train_user_seq = {}
    val_user_seq = {}
    test_user_seq = {}
    
    for u in User:
        seq = User[u]
        if len(seq) < 3: continue
        train_user_seq[u] = seq[:-2]
        val_user_seq[u] = seq[:-1] 
        test_user_seq[u] = seq[:] 
        
    return [train_user_seq, val_user_seq, test_user_seq], num_users, num_items, item_novelty_score


# Dataset
class SASRecDataset(Dataset):
    def __init__(self, user_seq, num_items, train=True):
        self.user_seq = user_seq
        self.users = list(user_seq.keys())
        self.num_items = num_items
        self.train = train
        
    def __len__(self):
        return len(self.users)
        
    def __getitem__(self, idx):
        user = self.users[idx]
        seq = self.user_seq[user]
        
        # 训练模式：需要构造 (Input, PosTarget, NegTarget)
        if self.train:

            seq_len = len(seq)

            
            input_ids = np.zeros(MAX_LEN, dtype=int)
            pos_ids = np.zeros(MAX_LEN, dtype=int)
            neg_ids = np.zeros(MAX_LEN, dtype=int)
            
            # 取最后 MAX_LEN 个
            start_idx = max(0, seq_len - MAX_LEN)
            curr_seq = seq[start_idx:]
            
            for i, item_id in enumerate(curr_seq):
                pass 
            
            input_seq = np.zeros(MAX_LEN, dtype=int)
            pos_seq = np.zeros(MAX_LEN, dtype=int)
            neg_seq = np.zeros(MAX_LEN, dtype=int)
            
            # 实际序列长度
            curr_len = len(curr_seq)
            

            input_seq[-curr_len:] = curr_seq
            
            nxt_items = curr_seq[1:] # 真实的下一个
            inp_items = curr_seq[:-1] # 输入
            
            # Pad
            pad_len = MAX_LEN - len(inp_items)
            if pad_len < 0:
                inp_items = inp_items[-MAX_LEN:]
                nxt_items = nxt_items[-MAX_LEN:]
                pad_len = 0
                
            input_seq[pad_len:] = inp_items
            pos_seq[pad_len:] = nxt_items

            for i in range(pad_len, MAX_LEN):
                while True:
                    neg = np.random.randint(1, self.num_items + 1)
                    if neg not in seq: 
                        neg_seq[i] = neg
                        break
                        
            return torch.LongTensor(input_seq), torch.LongTensor(pos_seq), torch.LongTensor(neg_seq)
            
        else:
            seq = seq[-MAX_LEN:]
            input_seq = np.zeros(MAX_LEN, dtype=int)
            input_seq[-len(seq):] = seq
            return torch.LongTensor([user]), torch.LongTensor(input_seq)

# Model: SASRec (Transformer)

class PointWiseFeedForward(nn.Module):
    def __init__(self, hidden_units, dropout_rate):
        super(PointWiseFeedForward, self).__init__()
        self.conv1 = nn.Conv1d(hidden_units, hidden_units, kernel_size=1)
        self.dropout1 = nn.Dropout(p=dropout_rate)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(hidden_units, hidden_units, kernel_size=1)
        self.dropout2 = nn.Dropout(p=dropout_rate)

    def forward(self, inputs):
        outputs = self.dropout2(self.conv2(self.relu(self.dropout1(self.conv1(inputs.transpose(-1, -2))))))
        outputs = outputs.transpose(-1, -2) 
        outputs += inputs
        return outputs

class SASRec(nn.Module):
    def __init__(self, num_users, num_items, args):
        super(SASRec, self).__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.dev = DEVICE
        
        
        self.item_emb = nn.Embedding(self.num_items + 1, args['embed_dim'], padding_idx=0)
        self.pos_emb = nn.Embedding(args['max_len'], args['embed_dim']) 
        self.emb_dropout = nn.Dropout(p=args['dropout'])
        
        self.attention_layernorms = nn.ModuleList() 
        self.attention_layers = nn.ModuleList()
        self.forward_layernorms = nn.ModuleList()
        self.forward_layers = nn.ModuleList()
        
        self.last_layernorm = nn.LayerNorm(args['embed_dim'], eps=1e-8)

        for _ in range(args['blocks']):
            new_attn_layernorm = nn.LayerNorm(args['embed_dim'], eps=1e-8)
            self.attention_layernorms.append(new_attn_layernorm)
            
            new_attn_layer = nn.MultiheadAttention(args['embed_dim'],
                                                   args['heads'],
                                                   args['dropout'])
            self.attention_layers.append(new_attn_layer)
            
            new_fwd_layernorm = nn.LayerNorm(args['embed_dim'], eps=1e-8)
            self.forward_layernorms.append(new_fwd_layernorm)
            
            new_fwd_layer = PointWiseFeedForward(args['embed_dim'], args['dropout'])
            self.forward_layers.append(new_fwd_layer)
            
    def log2feats(self, log_seqs):

        seqs = self.item_emb(log_seqs) # [batch, len, dim]
        seqs *= self.item_emb.embedding_dim ** 0.5 
        

        positions = np.tile(np.array(range(log_seqs.shape[1])), [log_seqs.shape[0], 1])
        seqs += self.pos_emb(torch.LongTensor(positions).to(self.dev))
        seqs = self.emb_dropout(seqs)
        

        timeline_mask = (log_seqs == 0)
        
        sz = log_seqs.shape[1]
        attn_mask = torch.triu(torch.ones(sz, sz), diagonal=1).bool().to(self.dev)
        
        # Transformer Blocks
        seqs = seqs.transpose(0, 1)
        
        for i in range(len(self.attention_layers)):
            
            Q = self.attention_layernorms[i](seqs)
            mha_outputs, _ = self.attention_layers[i](Q, seqs, seqs, attn_mask=attn_mask)

            seqs = Q + mha_outputs
            
            seqs = self.forward_layernorms[i](seqs)
            seqs = self.forward_layers[i](seqs)
            
        seqs = self.last_layernorm(seqs)
        
        # 变回 [batch, len, dim]
        return seqs.transpose(0, 1)

    def forward(self, user_seqs, pos_seqs, neg_seqs):

        
        log_feats = self.log2feats(user_seqs) 
        
        pos_embs = self.item_emb(pos_seqs)
        neg_embs = self.item_emb(neg_seqs)
        
        
        pos_logits = (log_feats * pos_embs).sum(dim=-1)
        neg_logits = (log_feats * neg_embs).sum(dim=-1)
        
        return pos_logits, neg_logits

    def predict(self, user_seqs, item_indices):
        
        
        log_feats = self.log2feats(user_seqs) 
        final_feat = log_feats[:, -1, :] 
        
        item_embs = self.item_emb(item_indices) 
        

        logits = item_embs.matmul(final_feat.unsqueeze(-1)).squeeze(-1)
        
        return logits


# 评估
def evaluate(model, dataset, args, item_novelty_score):
    model.eval()
    dataloader = DataLoader(dataset, batch_size=64, shuffle=False)
    
    metrics = {'Recall@10': [], 'nDCG@10': [], 'Novelty@10': [], 'AUC': []}
    
    recommended_items_set = set()

    all_users = dataset.users
    user_seq_map = dataset.user_seq
    num_items = dataset.num_items
    
    with torch.no_grad():
        for batch in dataloader:
            users, seqs = batch
            users = users.to(DEVICE)
            seqs = seqs.to(DEVICE)
            inputs = seqs[:, :-1]
            targets = seqs[:, -1]
            
            cand_ids = []
            for i in range(len(users)):
                u = users[i].item()
                target_item = targets[i].item()
                u_history = set(user_seq_map[u])
                
                cands = [target_item]
                while len(cands) < 100:
                    neg = np.random.randint(1, num_items + 1)
                    if neg not in u_history and neg != target_item:
                        cands.append(neg)
                cand_ids.append(cands)
                
            cand_tensor = torch.LongTensor(cand_ids).to(DEVICE) 
            scores = model.predict(inputs, cand_tensor)

            pos_scores = scores[:, 0].unsqueeze(1) # [Batch, 1]
            neg_scores = scores[:, 1:]             # [Batch, 99]
            

            batch_auc = (pos_scores > neg_scores).float().mean(dim=1).cpu().numpy()
            metrics['AUC'].extend(batch_auc)

            ranks = scores.argsort(dim=1, descending=True)
            
            ranks_np = ranks.cpu().numpy()
            cand_ids_np = np.array(cand_ids)
            
            for i, r in enumerate(ranks_np):

                top10_indices = r[:10]
                top10_items = cand_ids_np[i][top10_indices]
                
                # 记录覆盖率
                for item in top10_items:
                    recommended_items_set.add(item)
                
                # 计算 Novelty (Top-10 的平均新颖度)
                nov_score = np.mean([item_novelty_score.get(item, 0) for item in top10_items])
                metrics['Novelty@10'].append(nov_score)
                
                # 计算 Recall & nDCG (Target 在 index 0)
                rank_pos = np.where(r == 0)[0][0]
                
                if rank_pos < 10:
                    metrics['Recall@10'].append(1.0)
                    metrics['nDCG@10'].append(1.0 / np.log2(rank_pos + 2))
                else:
                    metrics['Recall@10'].append(0.0)
                    metrics['nDCG@10'].append(0.0)

    res = {k: np.mean(v) for k, v in metrics.items()}
    # 计算全局 Coverage
    res['Coverage@10'] = len(recommended_items_set) / num_items
    return res


# 可视化

def plot_results(loss_history, metrics):
    # 设置风格
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 图 1: Training Loss
    ax1.plot(loss_history, label='SASRec Training Loss', color='#1f77b4', linewidth=2.5)
    ax1.set_title('SASRec Training Loss Convergence', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Epochs', fontsize=12)
    ax1.set_ylabel('BCE Loss', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(fontsize=12)
    
    # 图 2: Final Metrics (双坐标轴)
    left_metrics = ['Recall@10', 'nDCG@10', 'Coverage@10', 'AUC']
    right_metrics = ['Novelty@10']
    
    labels = left_metrics + right_metrics
    data_left = [metrics[k] for k in left_metrics]
    data_right = [metrics[k] for k in right_metrics]
    
    x = np.arange(len(labels))
    

    ax2_left = ax2

    colors = ['#2ca02c', '#ff7f0e', '#d62728', '#17becf']
    bars1 = ax2_left.bar(x[:4], data_left, color=colors, alpha=0.9, label='Accuracy/Coverage')
    ax2_left.set_ylabel('Score (0-1)', fontsize=12, fontweight='bold')
    ax2_left.set_ylim(0, 1.15) 
    

    ax2_right = ax2.twinx()
    bars2 = ax2_right.bar(x[4:], data_right, color=['#9467bd'], alpha=0.9, label='Novelty')
    ax2_right.set_ylabel('Novelty Score (Self-Info)', fontsize=12, fontweight='bold', rotation=270, labelpad=15)
    ax2_right.set_ylim(0, 16) 
    
    # 设置 X 轴
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=11, fontweight='bold')
    ax2.set_title('SASRec Evaluation Metrics', fontsize=14, fontweight='bold')
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax2_left.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                      f'{height:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
    for bar in bars2:
        height = bar.get_height()
        ax2_right.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                       f'{height:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('sasrec_report_optimized_others.png', dpi=300)
    print(">>> Visualization saved to 'sasrec_report_optimized.png'")


if __name__ == "__main__":

    data_bundle, num_users, num_items, item_novelty = data_partition('ratings.dat')
    train_seq, val_seq, test_seq = data_bundle
    
    print(f"Num Users: {num_users}, Num Items: {num_items}")
    

    train_ds = SASRecDataset(train_seq, num_items, train=True)
    val_ds = SASRecDataset(val_seq, num_items, train=False) # 验证集
    test_ds = SASRecDataset(test_seq, num_items, train=False)
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)


    model_args = {
        'embed_dim': EMBED_DIM,
        'max_len': MAX_LEN,
        'blocks': NUM_BLOCKS,
        'heads': NUM_HEADS,
        'dropout': DROPOUT_RATE
    }
    model = SASRec(num_users, num_items, model_args).to(DEVICE)
    


    optimizer = torch.optim.Adam(model.parameters(), lr=LR, betas=(0.9, 0.98))
    bce_criterion = nn.BCEWithLogitsLoss() 
    
    best_recall = 0.0
    loss_history = []
    
    print(">>> Start Training SASRec...")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        start_time = time.time()
        
        for batch in train_loader:
            log_seqs, pos_seqs, neg_seqs = batch
            log_seqs, pos_seqs, neg_seqs = log_seqs.to(DEVICE), pos_seqs.to(DEVICE), neg_seqs.to(DEVICE)
            
            optimizer.zero_grad()
            pos_logits, neg_logits = model(log_seqs, pos_seqs, neg_seqs)
            
            pos_labels = torch.ones_like(pos_logits)
            neg_labels = torch.zeros_like(neg_logits)
            
            indices = np.where(log_seqs.cpu().numpy() != 0)
            loss = bce_criterion(pos_logits[indices], pos_labels[indices]) + \
                   bce_criterion(neg_logits[indices], neg_labels[indices])
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_loss = total_loss/len(train_loader)
        loss_history.append(avg_loss)
        print(f"Epoch {epoch} | Loss: {avg_loss:.4f} | Time: {time.time()-start_time:.1f}s")
        
        if epoch % 1 == 0:
            print(">>> Evaluating on Val Set...")
            res = evaluate(model, val_ds, model_args, item_novelty)
            print(f"    [Val] Recall@10: {res['Recall@10']:.4f} | nDCG@10: {res['nDCG@10']:.4f}")

            if res['Recall@10'] > best_recall:
                best_recall = res['Recall@10']
                torch.save(model.state_dict(), 'sasrec_best.pth')
                print("    >>> Best Model Saved (Based on Recall)!")
                
    print("\n>>> Final Test on Best Model...")
    model.load_state_dict(torch.load('sasrec_best.pth'))
    test_res = evaluate(model, test_ds, model_args, item_novelty)
    
    print(f"Test Recall@10:   {test_res['Recall@10']:.4f}")
    print(f"Test nDCG@10:     {test_res['nDCG@10']:.4f}")
    print(f"Test AUC:         {test_res['AUC']:.4f}")
    print(f"Test Novelty@10:  {test_res['Novelty@10']:.4f}")
    print(f"Test Coverage@10: {test_res['Coverage@10']:.4f}")
    

    plot_results(loss_history, test_res)