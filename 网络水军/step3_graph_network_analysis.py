"""
图网络分析模块
构建用户-商品关系网络，发现水军团伙
使用 PageRank + Louvain社区检测 + 中心性分析
针对大规模数据优化内存使用
"""

import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms import community
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class GraphNetworkAnalyzer:
    """图网络分析器（内存优化版）"""
    
    def __init__(self):
        self.G = None
        self.user_product_graph = None
        self.user_similarity_graph = None
        
    def build_bipartite_graph(self, data):
        """构建用户-商品二部图"""
        print("\n" + "="*70)
        print("【构建图1】用户-商品二部图")
        print("="*70)
        print("原理: 发现同时评论多个商品的异常用户群体")
        
        G = nx.Graph()
        
        if '评论者' in data.columns:
            users = data['评论者'].fillna('匿名用户').astype(str)
        else:
            users = [f"用户{i}" for i in range(len(data))]
        
        if '商品ID' in data.columns:
            products = data['商品ID'].fillna('商品1').astype(str)
        else:
            products = ['商品1'] * len(data)
        
        edge_count = 0
        for user, product in zip(users, products):
            G.add_node(f"U_{user}", bipartite=0, type='user')
            G.add_node(f"P_{product}", bipartite=1, type='product')
            G.add_edge(f"U_{user}", f"P_{product}")
            edge_count += 1
        
        self.user_product_graph = G
        
        user_nodes = [n for n, d in G.nodes(data=True) if d['type'] == 'user']
        product_nodes = [n for n, d in G.nodes(data=True) if d['type'] == 'product']
        
        print(f"\n结果:")
        print(f"  ✓ 用户节点: {len(user_nodes):,} 个")
        print(f"  ✓ 商品节点: {len(product_nodes):,} 个")
        print(f"  ✓ 评论关系边: {edge_count:,} 条")
        
        user_degrees = dict(G.degree([n for n in user_nodes]))
        top_users = sorted(user_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print(f"\n  评论最多的10个用户:")
        for user, degree in top_users:
            print(f"    {user}: {degree} 条评论")
        
        return G
    
    def build_user_similarity_graph_efficient(self, features, threshold=0.75, 
                                             batch_size=1000, max_edges=50000):
        """
        构建用户相似度图（内存高效版本）
        使用分批计算 + 采样策略避免内存溢出
        """
        print("\n" + "="*70)
        print("【构建图2】用户相似度网络（内存优化）")
        print("="*70)
        print(f"原理: 相似度>{threshold}的用户可能属于同一水军团伙")
        print(f"策略: 分批计算 + 边数限制，避免内存溢出")
        
        n_samples = features.shape[0]
        G = nx.Graph()
        
        # 添加所有节点
        for i in range(n_samples):
            G.add_node(i)
        
        print(f"\n处理进度:")
        print(f"  总样本数: {n_samples:,}")
        print(f"  批次大小: {batch_size}")
        print(f"  最大边数: {max_edges:,}")
        
        edge_count = 0
        total_batches = (n_samples + batch_size - 1) // batch_size
        
        # 分批计算相似度
        for batch_idx in range(0, n_samples, batch_size):
            batch_end = min(batch_idx + batch_size, n_samples)
            batch_features = features.iloc[batch_idx:batch_end]
            
            # 只与后续样本计算（避免重复）
            for compare_idx in range(batch_end, n_samples, batch_size):
                compare_end = min(compare_idx + batch_size, n_samples)
                compare_features = features.iloc[compare_idx:compare_end]
                
                # 计算当前批次的相似度
                similarities = cosine_similarity(batch_features, compare_features)
                
                # 找到高相似度对
                high_sim_pairs = np.argwhere(similarities > threshold)
                
                for i, j in high_sim_pairs:
                    if edge_count >= max_edges:
                        print(f"\n  ⚠️  达到最大边数限制 {max_edges:,}，停止添加")
                        break
                    
                    node_i = batch_idx + i
                    node_j = compare_idx + j
                    sim_value = similarities[i, j]
                    
                    G.add_edge(node_i, node_j, weight=sim_value)
                    edge_count += 1
                
                if edge_count >= max_edges:
                    break
            
            # 显示进度
            current_batch = (batch_idx // batch_size) + 1
            if current_batch % 5 == 0 or current_batch == total_batches:
                print(f"  进度: {current_batch}/{total_batches} 批次, "
                      f"已添加边: {edge_count:,}")
            
            if edge_count >= max_edges:
                break
        
        self.user_similarity_graph = G
        
        print(f"\n结果:")
        print(f"  ✓ 节点数: {G.number_of_nodes():,}")
        print(f"  ✓ 边数: {edge_count:,}")
        
        if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
            print(f"  ✓ 平均度: {np.mean([d for n, d in G.degree()]):.2f}")
            print(f"  ✓ 连通分量数: {nx.number_connected_components(G)}")
            
            isolated = list(nx.isolates(G))
            print(f"  ✓ 孤立节点: {len(isolated):,} 个（可能是正常用户）")
        else:
            print(f"  ⚠️  未找到高相似度边，尝试降低阈值")
        
        return G
    
    def build_user_similarity_graph_sampling(self, features, threshold=0.75, 
                                           sample_size=5000):
        """
        采样版本：随机采样部分数据构建图
        适用于超大规模数据
        """
        print("\n" + "="*70)
        print("【构建图2】用户相似度网络（采样版本）")
        print("="*70)
        print(f"原理: 相似度>{threshold}的用户可能属于同一水军团伙")
        print(f"策略: 随机采样 {sample_size:,} 个样本进行分析")
        
        n_samples = features.shape[0]
        
        # 随机采样
        if n_samples > sample_size:
            print(f"\n采样策略:")
            print(f"  原始样本: {n_samples:,}")
            print(f"  采样数量: {sample_size:,}")
            print(f"  采样比例: {sample_size/n_samples*100:.1f}%")
            
            sample_indices = np.random.choice(n_samples, sample_size, replace=False)
            sample_indices = np.sort(sample_indices)
            features_sample = features.iloc[sample_indices]
            
            # 创建索引映射
            index_mapping = {i: idx for i, idx in enumerate(sample_indices)}
        else:
            features_sample = features
            sample_indices = np.arange(n_samples)
            index_mapping = {i: i for i in range(n_samples)}
        
        # 计算相似度矩阵
        print(f"\n计算相似度矩阵...")
        similarity_matrix = cosine_similarity(features_sample)
        
        # 构建图
        G = nx.Graph()
        edge_count = 0
        
        print(f"构建网络图...")
        for i in range(len(features_sample)):
            for j in range(i + 1, len(features_sample)):
                if similarity_matrix[i, j] > threshold:
                    # 使用原始索引
                    orig_i = index_mapping[i]
                    orig_j = index_mapping[j]
                    G.add_edge(orig_i, orig_j, weight=similarity_matrix[i, j])
                    edge_count += 1
        
        self.user_similarity_graph = G
        
        print(f"\n结果:")
        print(f"  ✓ 节点数: {G.number_of_nodes():,}")
        print(f"  ✓ 边数: {edge_count:,}")
        
        if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
            print(f"  ✓ 平均度: {np.mean([d for n, d in G.degree()]):.2f}")
            print(f"  ✓ 连通分量数: {nx.number_connected_components(G)}")
            
            isolated = list(nx.isolates(G))
            print(f"  ✓ 孤立节点: {len(isolated):,} 个")
        
        return G
    
    def detect_communities(self, G):
        """Louvain社区检测"""
        print("\n" + "="*70)
        print("【社区检测】Louvain算法")
        print("="*70)
        print("原理: 发现紧密连接的用户群体（水军团伙）")
        
        if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
            print("  ⚠️  图中没有边，跳过社区检测")
            return {}
        
        # Louvain社区检测
        communities = community.greedy_modularity_communities(G)
        
        node_to_community = {}
        for i, comm in enumerate(communities):
            for node in comm:
                node_to_community[node] = i
        
        print(f"\n结果:")
        print(f"  ✓ 发现社区数量: {len(communities)}")
        
        try:
            mod = community.modularity(G, communities)
            print(f"  ✓ 模块度: {mod:.4f}")
        except:
            print(f"  ✓ 模块度: 无法计算")
        
        community_sizes = [len(comm) for comm in communities]
        print(f"\n  社区规模统计:")
        print(f"    最大社区: {max(community_sizes):,} 个成员")
        print(f"    最小社区: {min(community_sizes):,} 个成员")
        print(f"    平均规模: {np.mean(community_sizes):.1f} 个成员")
        
        sorted_communities = sorted(enumerate(communities), 
                                   key=lambda x: len(x[1]), reverse=True)
        print(f"\n  前5大社区:")
        for i, (idx, comm) in enumerate(sorted_communities[:5], 1):
            print(f"    社区 {idx}: {len(comm):,} 个成员")
        
        return node_to_community
    
    def calculate_pagerank(self, G, alpha=0.85):
        """PageRank算法"""
        print("\n" + "="*70)
        print("【PageRank分析】识别核心节点")
        print("="*70)
        print("原理: 评分高的节点在网络中影响力大（可能是水军头目）")
        
        if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
            print("  ⚠️  图中没有边，跳过PageRank")
            return {}
        
        pagerank_scores = nx.pagerank(G, alpha=alpha)
        
        sorted_nodes = sorted(pagerank_scores.items(), 
                            key=lambda x: x[1], reverse=True)
        
        print(f"\n结果:")
        print(f"  ✓ 已计算 {len(pagerank_scores):,} 个节点的PageRank")
        
        print(f"\n  PageRank Top 10 节点:")
        for i, (node, score) in enumerate(sorted_nodes[:10], 1):
            print(f"    {i}. 节点 {node}: {score:.6f}")
        
        return pagerank_scores
    
    def calculate_centrality_metrics(self, G):
        """计算多种中心性指标"""
        print("\n" + "="*70)
        print("【中心性分析】多维度评估节点重要性")
        print("="*70)
        
        if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
            print("  ⚠️  图中没有边，跳过中心性分析")
            return {}
        
        metrics = {}
        
        print("  计算度中心性...")
        degree_centrality = nx.degree_centrality(G)
        metrics['degree'] = degree_centrality
        
        if G.number_of_nodes() < 1000:
            print("  计算接近中心性...")
            try:
                closeness_centrality = nx.closeness_centrality(G)
                metrics['closeness'] = closeness_centrality
            except:
                print("  ⚠️  接近中心性计算失败")
                metrics['closeness'] = {}
        else:
            print("  ⚠️  图太大，跳过接近中心性")
            metrics['closeness'] = {}
        
        if G.number_of_nodes() < 500:
            print("  计算介数中心性...")
            try:
                betweenness_centrality = nx.betweenness_centrality(G)
                metrics['betweenness'] = betweenness_centrality
            except:
                print("  ⚠️  介数中心性计算失败")
                metrics['betweenness'] = {}
        else:
            print("  ⚠️  图太大，跳过介数中心性")
            metrics['betweenness'] = {}
        
        print(f"\n结果:")
        print(f"  ✓ 度中心性: {len(metrics['degree']):,} 个节点")
        if metrics['closeness']:
            print(f"  ✓ 接近中心性: {len(metrics['closeness']):,} 个节点")
        if metrics['betweenness']:
            print(f"  ✓ 介数中心性: {len(metrics['betweenness']):,} 个节点")
        
        return metrics
    
    def identify_suspicious_patterns(self, G, communities, pagerank_scores):
        """识别可疑模式"""
        print("\n" + "="*70)
        print("【可疑模式识别】")
        print("="*70)
        
        suspicious_nodes = set()
        patterns = []
        
        if pagerank_scores:
            threshold = np.percentile(list(pagerank_scores.values()), 90)
            high_pr_nodes = [n for n, score in pagerank_scores.items() 
                           if score > threshold]
            suspicious_nodes.update(high_pr_nodes)
            patterns.append(f"高PageRank节点: {len(high_pr_nodes)} 个")
        
        if G.number_of_nodes() > 0:
            degrees = dict(G.degree())
            if len(degrees) > 0:
                avg_degree = np.mean(list(degrees.values()))
                std_degree = np.std(list(degrees.values()))
                high_degree_nodes = [n for n, d in degrees.items() 
                                   if d > avg_degree + 2 * std_degree]
                suspicious_nodes.update(high_degree_nodes)
                patterns.append(f"高度数节点: {len(high_degree_nodes)} 个")
        
        if communities:
            community_counts = Counter(communities.values())
            large_communities = [c for c, count in community_counts.items() 
                               if count > 10]
            large_comm_nodes = [n for n, c in communities.items() 
                              if c in large_communities]
            suspicious_nodes.update(large_comm_nodes)
            patterns.append(f"大型社区成员: {len(large_comm_nodes)} 个")
        
        print(f"\n识别到的可疑模式:")
        for pattern in patterns:
            print(f"  • {pattern}")
        
        print(f"\n总计可疑节点: {len(suspicious_nodes)} 个")
        
        return list(suspicious_nodes), patterns
    
    def visualize_network(self, G, communities=None, pagerank_scores=None,
                         suspicious_nodes=None, save_path='network_graph.png',
                         max_nodes_to_plot=1000):
        """可视化网络图（采样版本）"""
        print("\n" + "="*70)
        print("【网络可视化】")
        print("="*70)
        
        if G.number_of_nodes() == 0:
            print("  ⚠️  图中没有节点，跳过可视化")
            return
        
        # 如果节点太多，采样可视化
        if G.number_of_nodes() > max_nodes_to_plot:
            print(f"  节点数 ({G.number_of_nodes():,}) 超过限制，")
            print(f"  采样 {max_nodes_to_plot} 个节点进行可视化")
            
            # 优先采样度数高的节点
            degrees = dict(G.degree())
            sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            sample_nodes = [n for n, d in sorted_nodes[:max_nodes_to_plot]]
            G_sample = G.subgraph(sample_nodes).copy()
        else:
            G_sample = G
        
        fig, axes = plt.subplots(2, 2, figsize=(18, 16))
        
        # 计算布局
        print("  计算网络布局...")
        pos = nx.spring_layout(G_sample, k=0.5, iterations=50, seed=42)
        
        # 1. 基本网络结构
        ax = axes[0, 0]
        nx.draw_networkx_edges(G_sample, pos, alpha=0.2, ax=ax)
        nx.draw_networkx_nodes(G_sample, pos, node_size=30, node_color='lightblue', 
                              alpha=0.6, ax=ax)
        ax.set_title('网络整体结构', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        # 2. 社区检测结果
        ax = axes[0, 1]
        if communities and len(communities) > 0:
            unique_communities = set(communities.values())
            colors = plt.cm.tab20(np.linspace(0, 1, min(len(unique_communities), 20)))
            color_map = {comm: colors[i % 20] for i, comm in enumerate(unique_communities)}
            
            node_colors = [color_map.get(communities.get(n, 0), [0.5, 0.5, 0.5, 1.0]) 
                          for n in G_sample.nodes()]
            
            nx.draw_networkx_edges(G_sample, pos, alpha=0.2, ax=ax)
            nx.draw_networkx_nodes(G_sample, pos, node_size=30, node_color=node_colors,
                                  alpha=0.7, ax=ax)
            
            ax.set_title(f'社区检测结果 ({len(unique_communities)} 个社区)', 
                        fontsize=14, fontweight='bold')
        else:
            ax.text(0.5, 0.5, '无社区数据', ha='center', va='center',
                   transform=ax.transAxes, fontsize=16)
        ax.axis('off')
        
        # 3. PageRank重要性
        ax = axes[1, 0]
        if pagerank_scores and len(pagerank_scores) > 0:
            node_sizes = [pagerank_scores.get(n, 0) * 5000 for n in G_sample.nodes()]
            node_colors_pr = [pagerank_scores.get(n, 0) for n in G_sample.nodes()]
            
            nx.draw_networkx_edges(G_sample, pos, alpha=0.2, ax=ax)
            nodes = nx.draw_networkx_nodes(G_sample, pos, node_size=node_sizes,
                                          node_color=node_colors_pr,
                                          cmap='YlOrRd', alpha=0.7, ax=ax)
            
            plt.colorbar(nodes, ax=ax, label='PageRank分数')
            ax.set_title('PageRank节点重要性', fontsize=14, fontweight='bold')
        else:
            ax.text(0.5, 0.5, '无PageRank数据', ha='center', va='center',
                   transform=ax.transAxes, fontsize=16)
        ax.axis('off')
        
        # 4. 可疑节点标记
        ax = axes[1, 1]
        if suspicious_nodes and len(suspicious_nodes) > 0:
            sample_suspicious = [n for n in suspicious_nodes if n in G_sample.nodes()]
            normal_nodes = [n for n in G_sample.nodes() if n not in sample_suspicious]
            
            nx.draw_networkx_edges(G_sample, pos, alpha=0.2, ax=ax)
            
            if normal_nodes:
                nx.draw_networkx_nodes(G_sample, pos, nodelist=normal_nodes,
                                      node_size=20, node_color='lightblue',
                                      alpha=0.5, ax=ax, label='正常')
            
            if sample_suspicious:
                nx.draw_networkx_nodes(G_sample, pos, nodelist=sample_suspicious,
                                      node_size=100, node_color='red',
                                      alpha=0.8, ax=ax, label='可疑', 
                                      node_shape='^')
            
            ax.legend(loc='upper right', fontsize=10)
            ax.set_title(f'可疑节点识别 ({len(sample_suspicious)} 个)',
                        fontsize=14, fontweight='bold')
        else:
            ax.text(0.5, 0.5, '无可疑节点数据', ha='center', va='center',
                   transform=ax.transAxes, fontsize=16)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 网络图已保存: {save_path}")
        plt.close()
    
    def generate_network_report(self, G, communities, pagerank_scores, 
                               centrality_metrics, suspicious_nodes):
        """生成网络分析报告"""
        print("\n" + "="*70)
        print("【生成分析报告】")
        print("="*70)
        
        report = []
        report.append("="*70)
        report.append("图网络分析报告")
        report.append("="*70)
        report.append("")
        
        report.append("1. 网络基本统计")
        report.append("-"*70)
        report.append(f"  节点数: {G.number_of_nodes():,}")
        report.append(f"  边数: {G.number_of_edges():,}")
        if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
            report.append(f"  平均度: {np.mean([d for n, d in G.degree()]):.2f}")
            report.append(f"  图密度: {nx.density(G):.6f}")
            report.append(f"  连通分量数: {nx.number_connected_components(G)}")
        report.append("")
        
        if communities:
            report.append("2. 社区检测结果")
            report.append("-"*70)
            report.append(f"  社区数量: {len(set(communities.values()))}")
            community_sizes = Counter(communities.values())
            report.append(f"  最大社区规模: {max(community_sizes.values()):,}")
            report.append(f"  平均社区规模: {np.mean(list(community_sizes.values())):.1f}")
            report.append("")
        
        if pagerank_scores:
            report.append("3. PageRank Top 20 节点")
            report.append("-"*70)
            sorted_pr = sorted(pagerank_scores.items(), 
                             key=lambda x: x[1], reverse=True)[:20]
            for i, (node, score) in enumerate(sorted_pr, 1):
                report.append(f"  {i:2d}. 节点 {node}: {score:.6f}")
            report.append("")
        
        if centrality_metrics:
            report.append("4. 中心性分析")
            report.append("-"*70)
            for metric_name, metric_values in centrality_metrics.items():
                if metric_values:
                    report.append(f"  {metric_name.capitalize()} 中心性:")
                    sorted_metric = sorted(metric_values.items(),
                                         key=lambda x: x[1], reverse=True)[:5]
                    for node, value in sorted_metric:
                        report.append(f"    节点 {node}: {value:.6f}")
            report.append("")
        
        if suspicious_nodes:
            report.append("5. 可疑节点列表")
            report.append("-"*70)
            report.append(f"  总计: {len(suspicious_nodes)} 个可疑节点")
            report.append(f"  节点ID: {suspicious_nodes[:50]}")
            if len(suspicious_nodes) > 50:
                report.append(f"  ... 还有 {len(suspicious_nodes) - 50} 个")
            report.append("")
        
        report.append("="*70)
        
        report_text = '\n'.join(report)
        with open('network_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"  ✓ 报告已保存: network_analysis_report.txt")
        
        return report_text


def main():
    """主函数"""
    print("\n" + "🕸️"*35)
    print("\n" + " "*15 + "步骤3：图网络分析")
    print(" "*8 + "构建关系网络，发现水军团伙和核心节点！")
    print("\n" + "🕸️"*35)
    
    # 1. 加载数据
    print("\n【阶段1】加载数据")
    print("-"*70)
    
    try:
        original_data = pd.read_excel("data120.xlsx")
        print(f"✅ 加载原始数据")
        print(f"   - 文件: data120.xlsx")
        print(f"   - 规模: {original_data.shape[0]:,} 行")
        
        features = pd.read_csv("advanced_features.csv")
        print(f"✅ 加载特征数据")
        print(f"   - 文件: advanced_features.csv")
        print(f"   - 规模: {features.shape[0]:,} 行 × {features.shape[1]} 列")
        
    except FileNotFoundError as e:
        print(f"❌ 错误：找不到文件")
        print(f"   {e}")
        print("   请先运行前面的步骤")
        return
    
    # 2. 初始化分析器
    print("\n【阶段2】构建网络图")
    print("-"*70)
    
    analyzer = GraphNetworkAnalyzer()
    
    # 构建二部图
    bipartite_graph = analyzer.build_bipartite_graph(original_data)
    
    # 构建用户相似度图（采样版本，避免内存溢出）
    sample_size = min(5000, features.shape[0])
    similarity_graph = analyzer.build_user_similarity_graph_sampling(
        features, threshold=0.75, sample_size=sample_size
    )
    
    # 3. 社区检测
    print("\n【阶段3】社区检测")
    print("-"*70)
    communities = analyzer.detect_communities(similarity_graph)
    
    # 4. PageRank分析
    print("\n【阶段4】PageRank分析")
    print("-"*70)
    pagerank_scores = analyzer.calculate_pagerank(similarity_graph)
    
    # 5. 中心性分析
    print("\n【阶段5】中心性分析")
    print("-"*70)
    centrality_metrics = analyzer.calculate_centrality_metrics(similarity_graph)
    
    # 6. 识别可疑模式
    print("\n【阶段6】识别可疑模式")
    print("-"*70)
    suspicious_nodes, patterns = analyzer.identify_suspicious_patterns(
        similarity_graph, communities, pagerank_scores
    )
    
    # 7. 保存结果
    print("\n【阶段7】保存分析结果")
    print("-"*70)
    
    node_data = pd.DataFrame({
        'node_id': list(similarity_graph.nodes()),
        'degree': [similarity_graph.degree(n) for n in similarity_graph.nodes()],
        'community': [communities.get(n, -1) for n in similarity_graph.nodes()],
        'pagerank': [pagerank_scores.get(n, 0) for n in similarity_graph.nodes()],
        'is_suspicious': [n in suspicious_nodes for n in similarity_graph.nodes()]
    })
    
    if centrality_metrics.get('degree'):
        node_data['degree_centrality'] = [
            centrality_metrics['degree'].get(n, 0) 
            for n in similarity_graph.nodes()
        ]
    
    node_data.to_csv("network_node_analysis.csv", index=False)
    print(f"✅ 节点分析结果已保存")
    print(f"   - 文件: network_node_analysis.csv")
    
    # 8. 可视化
    print("\n【阶段8】生成可视化")
    print("-"*70)
    analyzer.visualize_network(
        similarity_graph, communities, pagerank_scores, 
        suspicious_nodes, save_path='network_graph.png'
    )
    
    # 9. 生成报告
    print("\n【阶段9】生成分析报告")
    print("-"*70)
    report = analyzer.generate_network_report(
        similarity_graph, communities, pagerank_scores,
        centrality_metrics, suspicious_nodes
    )
    
    # 10. 总结
    print("\n" + "="*70)
    print("✅ 图网络分析完成！")
    print("="*70)
    
    print("\n📊 分析总结:")
    print(f"   • 网络节点: {similarity_graph.number_of_nodes():,} 个")
    print(f"   • 网络边: {similarity_graph.number_of_edges():,} 条")
    if communities:
        print(f"   • 发现社区: {len(set(communities.values()))} 个")
    print(f"   • 可疑节点: {len(suspicious_nodes)} 个")
    
    print(f"\n💡 说明:")
    print(f"   由于样本量较大（{features.shape[0]:,}条），")
    print(f"   采用采样策略（{sample_size:,}条）进行分析")
    
    print(f"\n📁 生成的文件:")
    print(f"   • network_node_analysis.csv - 节点属性数据")
    print(f"   • network_graph.png - 网络可视化")
    print(f"   • network_analysis_report.txt - 详细分析报告")
    
    print(f"\n🚀 下一步:")
    print(f"   运行集成学习模型:")
    print(f"   python step4_ensemble_learning.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()