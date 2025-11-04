"""
Meetup 信息检索实验 - 向量空间模型检索
基于TF-IDF计算文档-查询相似度，使用余弦相似度排序返回Top-N结果
"""

import json
import math
import time
from pathlib import Path
from collections import defaultdict, Counter

# ==================== 1. TF-IDF计算模块 ====================

def calculate_tf(term_count, total_terms):
    """
    计算词项频率(TF)
    :param term_count: 词项在文档中出现次数
    :param total_terms: 文档总词数
    :return: TF值
    """
    return 1+math.log10(term_count / total_terms) if total_terms > 0 else 0


def calculate_idf(total_docs, doc_freq):
    """
    计算逆文档频率(IDF) - 使用以10为底的对数
    :param total_docs: 文档总数
    :param doc_freq: 包含该词项的文档数
    :return: IDF值
    """
    return math.log10(total_docs / doc_freq )


def build_document_vectors(inverted_index, doc_lengths, sample_size=None):
    """
    构建所有文档的TF-IDF向量
    :param inverted_index: 倒排索引 {term: {docID: [positions]}}
    :param doc_lengths: 文档长度字典 {docID: 总词数}
    :param sample_size: 采样文档数量(None表示全部文档)
    :return: {docID: {term: tfidf_value}}
    """
    print("[构建] 文档TF-IDF向量...")
    start = time.perf_counter()
    
    # 如果指定采样,只处理部分文档
    if sample_size and sample_size < len(doc_lengths):
        sampled_docs = set(list(doc_lengths.keys())[:sample_size])
        print(f"  采样模式: {sample_size}/{len(doc_lengths)} 文档")
    else:
        sampled_docs = None
    
    total_docs = len(doc_lengths)
    doc_vectors = defaultdict(dict)
    
    # 对每个词项计算IDF
    for term, postings in inverted_index.items():
        doc_freq = len(postings)
        idf = calculate_idf(total_docs, doc_freq)
        
        # 对包含该词项的每个文档计算TF-IDF
        for doc_id, positions in postings.items():
            # 如果使用采样,跳过不在采样集中的文档
            if sampled_docs and doc_id not in sampled_docs:
                continue
                
            term_count = len(positions)
            total_terms = doc_lengths.get(doc_id, 1)
            tf = calculate_tf(term_count, total_terms)
            tfidf = tf * idf
            
            doc_vectors[doc_id][term] = tfidf
    
    elapsed = time.perf_counter() - start
    print(f"  文档数: {len(doc_vectors)}, 耗时: {elapsed:.4f}秒\n")
    
    return doc_vectors


def calculate_doc_lengths(inverted_index):
    """
    计算每个文档的总词数
    :param inverted_index: 倒排索引
    :return: {docID: 总词数}
    """
    print("[统计] 文档长度...")
    doc_lengths = defaultdict(int)
    
    for term, postings in inverted_index.items():
        for doc_id, positions in postings.items():
            doc_lengths[doc_id] += len(positions)
    
    print(f"  文档数: {len(doc_lengths)}\n")
    return doc_lengths


# ==================== 2. 向量空间检索模块 ====================

def build_query_vector(query_terms, inverted_index, total_docs):
    """
    构建查询向量(使用TF-IDF)
    :param query_terms: 查询词项列表
    :param inverted_index: 倒排索引
    :param total_docs: 文档总数
    :return: {term: tfidf_value}
    """
    query_vector = {}
    query_term_counts = Counter(query_terms)
    total_query_terms = len(query_terms)
    
    for term in query_terms:
        if term in inverted_index:
            # 计算查询中的TF
            tf = calculate_tf(query_term_counts[term], total_query_terms)
            # 计算IDF
            doc_freq = len(inverted_index[term])
            idf = calculate_idf(total_docs, doc_freq)
            # 计算TF-IDF
            query_vector[term] = tf * idf
        else:
            # 词项不在索引中,TF-IDF为0
            query_vector[term] = 0
    
    return query_vector


def cosine_similarity(doc_vector, query_vector):
    """
    计算余弦相似度
    :param doc_vector: 文档向量 {term: tfidf}
    :param query_vector: 查询向量 {term: tfidf}
    :return: 余弦相似度值
    """
    # 计算点积
    dot_product = sum(doc_vector.get(term, 0) * value 
                     for term, value in query_vector.items())
    
    # 计算向量模长
    doc_norm = math.sqrt(sum(value ** 2 for value in doc_vector.values()))
    query_norm = math.sqrt(sum(value ** 2 for value in query_vector.values()))
    
    # 避免除零
    if doc_norm == 0 or query_norm == 0:
        return 0
    
    return dot_product / (doc_norm * query_norm)


def vector_space_retrieval(query_vector, doc_vectors, top_n=20):
    """
    执行向量空间检索
    :param query_vector: 查询向量
    :param doc_vectors: 所有文档向量
    :param top_n: 返回Top-N结果
    :return: [(docID, similarity_score), ...]
    """
    print(f"[检索] 计算文档相似度...")
    start = time.perf_counter()
    
    # 计算所有文档与查询的相似度
    similarities = []
    for doc_id, doc_vector in doc_vectors.items():
        similarity = cosine_similarity(doc_vector, query_vector)
        if similarity > 0:  # 只保留相似度>0的文档
            similarities.append((doc_id, similarity))
    
    # 按相似度降序排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    elapsed = time.perf_counter() - start
    print(f"  匹配文档数: {len(similarities)}, 耗时: {elapsed:.4f}秒\n")
    
    return similarities[:top_n]


# ==================== 3. 结果输出模块 ====================

def get_document_terms(doc_id, doc_vector, top_k=5):
    """
    从文档向量中提取Top-K关键词项
    :param doc_id: 文档ID
    :param doc_vector: 文档TF-IDF向量 {term: tfidf}
    :param top_k: 返回前K个关键词
    :return: 关键词列表
    """
    sorted_terms = sorted(doc_vector.items(), key=lambda x: x[1], reverse=True)
    return [term for term, _ in sorted_terms[:top_k]]


def display_results(results, query_name, query_terms, doc_vectors):
    """
    展示检索结果（基于倒排表信息）
    :param results: 检索结果 [(docID, similarity), ...]
    :param query_name: 查询名称
    :param query_terms: 查询词项列表
    :param doc_vectors: 文档向量字典
    """
    print(f"{'='*80}")
    print(f"查询: {query_name}")
    print(f"词项: {', '.join(query_terms)}")
    print(f"{'='*80}\n")
    
    print(f"{'排名':<6s} {'文档ID':<15s} {'相似度':<12s} {'文档关键词'}")
    print(f"{'-'*80}")
    
    for rank, (doc_id, similarity) in enumerate(results, 1):
        # 提取文档的Top-5关键词
        doc_vector = doc_vectors.get(doc_id, {})
        keywords = get_document_terms(doc_id, doc_vector, top_k=5)
        keywords_str = ', '.join(keywords) if keywords else "无"
        
        print(f"{rank:<6d} {doc_id:<15s} {similarity:<12.6f} {keywords_str}")
    
    print()


# ==================== 4. 主实验流程 ====================

def main():
    # 设置路径
    base_path = Path(__file__).parent
    index_path = base_path / "inverted_index.json"
    
    # 加载倒排索引
    print("[加载] 倒排索引...")
    start = time.perf_counter()
    
    with open(index_path, 'r', encoding='utf-8') as f:
        inv_index_raw = json.load(f)
    
    # 转换为简化格式 {term: {docID: [positions]}}
    inverted_index = {}
    for term, data in inv_index_raw.items():
        inverted_index[term] = {}
        for posting in data["postings"]:
            doc_id = posting["doc"]
            positions = posting.get("positions", [])
            inverted_index[term][doc_id] = positions
    
    load_time = time.perf_counter() - start
    print(f"  词项数: {len(inverted_index)}")
    print(f"  加载耗时: {load_time:.4f}秒\n")
    
    # 计算文档长度
    doc_lengths = calculate_doc_lengths(inverted_index)
    total_docs = len(doc_lengths)
    
    # 构建文档TF-IDF向量 
    doc_vectors = build_document_vectors(inverted_index, doc_lengths)
    
    # 定义查询条件
    queries = [
        {
            "name": "纽约地区免费科技研讨会",
            "terms": ["new", "york", "free", "tech", "workshop"],
            "description": "寻找在纽约举办的免费技术工作坊/研讨会活动"
        },
        {
            "name": "线下美食品鉴活动",
            "terms": ["food", "tasting", "restaurant", "dinner"],
            "description": "筛选与美食品鉴、餐厅聚会相关的线下社交活动"
        },
        {
            "name": "Python编程学习小组",
            "terms": ["python", "programming", "coding", "learn", "beginner"],
            "description": "面向初学者的Python编程学习/练习活动"
        },
        {
            "name": "户外运动健身活动",
            "terms": ["outdoor", "hiking", "fitness", "running", "sports"],
            "description": "徒步、跑步、健身等户外运动相关活动"
        }
    ]
    
    # 验证查询词项是否存在
    print("[验证] 查询词项覆盖率...")
    valid_queries = []
    
    for query in queries:
        terms = query["terms"]
        found_terms = [t for t in terms if t in inverted_index]
        coverage = len(found_terms) / len(terms) * 100
        
        print(f"  '{query['name']}':")
        print(f"    查询词项: {', '.join(terms)}")
        print(f"    索引覆盖: {len(found_terms)}/{len(terms)} ({coverage:.1f}%)")
        
        if found_terms:  # 至少有一个词项存在
            query["valid_terms"] = found_terms
            valid_queries.append(query)
            print(f"    状态: ✓ 有效")
        else:
            print(f"    状态: ✗ 无效(所有词项均不在索引中)")
        print()
    
    if not valid_queries:
        print("错误: 没有有效的查询!")
        return
    
    # 执行向量空间检索
    print(f"\n{'='*80}")
    print("向量空间模型检索结果")
    print(f"{'='*80}\n")
    
    all_results = {}
    
    for query in valid_queries:
        query_name = query["name"]
        query_terms = query["valid_terms"]
        
        # 构建查询向量
        query_vector = build_query_vector(query_terms, inverted_index, total_docs)
        
        # 执行检索
        results = vector_space_retrieval(query_vector, doc_vectors, top_n=20)
        
        # 展示结果
        display_results(results, query_name, query_terms, doc_vectors)
        
        all_results[query_name] = results
    
    # ==================== 5. 结果分析 ====================
    
    print(f"\n{'='*80}")
    print("实验结果分析")
    print(f"{'='*80}\n")
    
    print("[1] 检索效果统计:")
    for query in valid_queries:
        query_name = query["name"]
        results = all_results[query_name]
        
        if results:
            avg_similarity = sum(sim for _, sim in results) / len(results)
            max_similarity = results[0][1]
            min_similarity = results[-1][1]
            
            print(f"  '{query_name}':")
            print(f"    匹配文档数: {len(results)}")
            print(f"    平均相似度: {avg_similarity:.6f}")
            print(f"    最高相似度: {max_similarity:.6f}")
            print(f"    最低相似度: {min_similarity:.6f}")
        else:
            print(f"  '{query_name}': 无匹配结果")
        print()
    
    

if __name__ == "__main__":
    main()
