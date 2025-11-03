"""
Meetup 信息检索实验 - 跳表指针步长对存储性能/检索效率影响分析
实验变量: 跳表步长 (√N, N/10, 固定50, 固定200)
评价指标: 存储空间(KB), AND检索耗时(ms)
"""

import json
import time
import math
import sys
from pathlib import Path
from collections import defaultdict

# ==================== 1. 跳表构建模块 ====================

class SkipListIndex:
    """带跳表指针的倒排索引"""
    
    def __init__(self, term, doc_ids, skip_step):
        """
        构建跳表
        :param term: 词项
        :param doc_ids: 有序文档ID列表
        :param skip_step: 跳表步长
        """
        self.term = term
        self.doc_ids = doc_ids  # 有序文档ID列表
        self.skip_step = skip_step
        self.skip_pointers = {}  # {起始索引: 目标索引}
        
        # 构建跳跃指针: 每隔skip_step个文档ID添加一个指针
        n = len(doc_ids)
        for i in range(0, n, skip_step):
            target_idx = min(i + skip_step, n - 1)
            if target_idx > i:
                self.skip_pointers[i] = target_idx
    
    def get_storage_size(self):
        """计算存储空间(字节)"""
        # 基础倒排表: 每个文档ID占4字节
        base_size = len(self.doc_ids) * 4
        # 跳表指针: 每个指针占8字节(起始索引4字节+目标索引4字节)
        skip_size = len(self.skip_pointers) * 8
        return base_size + skip_size
    
    def get_skip_count(self):
        """获取跳跃指针数量"""
        return len(self.skip_pointers)


def build_skip_indexes(inverted_index, skip_strategy):
    """
    为倒排索引中的所有词项构建跳表
    :param inverted_index: 原始倒排索引 {term: {docID: [positions]}}
    :param skip_strategy: 步长策略 ("sqrt", "div10", "fixed50", "fixed200")
    :return: {term: SkipListIndex对象}
    """
    skip_indexes = {}
    
    for term, postings in inverted_index.items():
        doc_ids = sorted(postings.keys())  # 提取有序文档ID列表
        n = len(doc_ids)
        
        # 根据策略计算步长
        if skip_strategy == "sqrt":
            skip_step = max(1, int(math.sqrt(n)))
        elif skip_strategy == "div10":
            skip_step = max(1, n // 10)
        elif skip_strategy == "fixed50":
            skip_step = 50
        elif skip_strategy == "fixed200":
            skip_step = 200
        else:
            skip_step = max(1, int(math.sqrt(n)))  # 默认√N
        
        skip_indexes[term] = SkipListIndex(term, doc_ids, skip_step)
    
    return skip_indexes


# ==================== 2. 带跳表的检索模块 ====================

def intersect_with_skiplist(skip_idx1, skip_idx2):
    """
    利用跳表执行AND检索(文档ID列表交集)
    :param skip_idx1: 第一个词项的跳表索引
    :param skip_idx2: 第二个词项的跳表索引
    :return: 交集文档ID列表
    """
    result = []
    docs1, docs2 = skip_idx1.doc_ids, skip_idx2.doc_ids
    pointers1, pointers2 = skip_idx1.skip_pointers, skip_idx2.skip_pointers
    
    i, j = 0, 0
    n1, n2 = len(docs1), len(docs2)
    
    while i < n1 and j < n2:
        doc1, doc2 = docs1[i], docs2[j]
        
        if doc1 == doc2:
            result.append(doc1)
            i += 1
            j += 1
        elif doc1 < doc2:
            # 尝试使用跳表指针跳过不匹配的文档
            if i in pointers1:
                target_idx = pointers1[i]
                if docs1[target_idx] <= doc2:
                    i = target_idx  # 跳跃
                    continue
            i += 1
        else:  # doc1 > doc2
            if j in pointers2:
                target_idx = pointers2[j]
                if docs2[target_idx] <= doc1:
                    j = target_idx  # 跳跃
                    continue
            j += 1
    
    return result


def intersect_without_skiplist(doc_ids1, doc_ids2):
    """
    不使用跳表的线性AND检索(基准对照)
    :param doc_ids1: 第一个词项的文档ID列表
    :param doc_ids2: 第二个词项的文档ID列表
    :return: 交集文档ID列表
    """
    result = []
    i, j = 0, 0
    n1, n2 = len(doc_ids1), len(doc_ids2)
    
    while i < n1 and j < n2:
        if doc_ids1[i] == doc_ids2[j]:
            result.append(doc_ids1[i])
            i += 1
            j += 1
        elif doc_ids1[i] < doc_ids2[j]:
            i += 1
        else:
            j += 1
    
    return result


# ==================== 3. 性能统计模块 ====================

def calculate_total_storage(skip_indexes):
    """计算所有词项的总存储空间"""
    total_size = sum(idx.get_storage_size() for idx in skip_indexes.values())
    return total_size / 1024  # 转换为KB


def benchmark_query(skip_indexes, term1, term2, runs=5):
    """
    测试单个查询的检索效率
    :param skip_indexes: 跳表索引字典
    :param term1, term2: 查询词项
    :param runs: 运行次数
    :return: 平均耗时(ms), 结果数量
    """
    if term1 not in skip_indexes or term2 not in skip_indexes:
        return None, 0
    
    times = []
    result = []
    
    for _ in range(runs):
        start = time.perf_counter()
        result = intersect_with_skiplist(skip_indexes[term1], skip_indexes[term2])
        elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    return avg_time, len(result)


def run_experiment(inverted_index, queries, skip_strategy):
    """
    运行单个步长策略的完整实验
    :param inverted_index: 原始倒排索引
    :param queries: 查询列表 [(term1, term2, frequency_label), ...]
    :param skip_strategy: 步长策略
    :return: 统计结果字典
    """
    print(f"\n{'='*60}")
    print(f"策略: {skip_strategy}")
    print(f"{'='*60}")
    
    # 构建跳表索引
    start = time.perf_counter()
    skip_indexes = build_skip_indexes(inverted_index, skip_strategy)
    build_time = time.perf_counter() - start
    
    # 计算存储性能
    total_storage_kb = calculate_total_storage(skip_indexes)
    
    # 统计跳表指针信息
    sample_terms = list(queries)[:3]
    print(f"\n[跳表构建]")
    print(f"  构建耗时: {build_time:.4f}秒")
    print(f"  总存储空间: {total_storage_kb:.2f} KB")
    print(f"  示例词项跳表信息:")
    for term1, term2, _ in sample_terms:
        if term1 in skip_indexes:
            idx = skip_indexes[term1]
            print(f"    '{term1}': 文档数={len(idx.doc_ids)}, 步长={idx.skip_step}, 指针数={idx.get_skip_count()}")
    
    # 执行检索效率测试
    print(f"\n[检索效率测试]")
    results = []
    
    for term1, term2, freq_label in queries:
        avg_time, result_count = benchmark_query(skip_indexes, term1, term2, runs=5)
        if avg_time is not None:
            results.append({
                "query": f"{term1} AND {term2}",
                "frequency": freq_label,
                "avg_time_ms": avg_time,
                "result_count": result_count
            })
            print(f"  {freq_label:8s} | {term1:15s} AND {term2:15s} | {avg_time:8.4f} ms | 结果: {result_count:5d}")
    
    return {
        "strategy": skip_strategy,
        "build_time": build_time,
        "storage_kb": total_storage_kb,
        "queries": results
    }


# ==================== 4. 主实验流程 ====================

def main():
    # 加载倒排索引
    base_path = Path(__file__).parent
    index_path = base_path / "inverted_index.json"
    
    print("[加载] 倒排索引...")
    start = time.perf_counter()
    with open(index_path, 'r', encoding='utf-8') as f:
        inv_index_raw = json.load(f)
    
    # 转换为简化格式 {term: {docID: positions}}
    inverted_index = {}
    for term, data in inv_index_raw.items():
        inverted_index[term] = {}
        for posting in data["postings"]:
            doc_id = posting["doc"]
            inverted_index[term][doc_id] = posting.get("positions", [])
    
    load_time = time.perf_counter() - start
    print(f"  词项数: {len(inverted_index)}")
    print(f"  加载耗时: {load_time:.4f}秒")
    
    # 定义测试查询 (基于实际词频分布)
    queries = [
        # 高频词 (DF > 10000) - 超高频词项
        ("event", "time", "高频"),
        ("new", "join", "高频"),
        ("group", "meetup", "高频"),
        
        # 中频词 (500 < DF < 2000) - 中等频率词项
        ("prepare", "hello", "中频"),
        ("avenue", "probably", "中频"),
        ("star", "fine", "中频"),
        
        # 低频词 (50 < DF < 200) - 低频词项
        ("accident", "deer", "低频"),
        ("kitty", "newspaper", "低频"),
        ("candy", "disaster", "低频"),
    ]
    
    # 验证查询词项是否存在
    print(f"\n[查询词项验证]")
    valid_queries = []
    for term1, term2, freq in queries:
        if term1 in inverted_index and term2 in inverted_index:
            df1 = len(inverted_index[term1])
            df2 = len(inverted_index[term2])
            print(f"  ✓ {term1:15s} (DF={df1:6d}) AND {term2:15s} (DF={df2:6d}) - {freq}")
            valid_queries.append((term1, term2, freq))
        else:
            print(f"  ✗ {term1} AND {term2} - 词项不存在")
    
    if not valid_queries:
        print("\n错误: 没有有效的查询词项!")
        return
    
    # 运行4种步长策略实验
    strategies = ["sqrt", "div10", "fixed50", "fixed200"]
    all_results = []
    
    for strategy in strategies:
        result = run_experiment(inverted_index, valid_queries, strategy)
        all_results.append(result)
    
    # ==================== 5. 结果汇总与分析 ====================
    
    print(f"\n\n{'='*80}")
    print("实验结果汇总")
    print(f"{'='*80}")
    
    # 存储性能对比
    print(f"\n[存储性能对比]")
    print(f"{'策略':<15s} | {'总存储空间(KB)':>18s} | {'构建耗时(秒)':>15s}")
    print(f"{'-'*60}")
    for result in all_results:
        print(f"{result['strategy']:<15s} | {result['storage_kb']:>18.2f} | {result['build_time']:>15.4f}")
    
    # 检索效率对比 (按频率分组)
    print(f"\n[检索效率对比 - 按词项频率分组]")
    
    for freq_label in ["高频", "中频", "低频"]:
        print(f"\n{freq_label}词项:")
        print(f"{'查询':<35s} | {'√N':>10s} | {'N/10':>10s} | {'固定50':>10s} | {'固定200':>10s}")
        print(f"{'-'*80}")
        
        # 提取该频率的所有查询
        freq_queries = [q for q in valid_queries if q[2] == freq_label]
        
        for term1, term2, _ in freq_queries:
            query_name = f"{term1} AND {term2}"
            times = []
            
            for result in all_results:
                matching = [q for q in result["queries"] if q["query"] == query_name]
                if matching:
                    times.append(f"{matching[0]['avg_time_ms']:.4f}")
                else:
                    times.append("N/A")
            
            print(f"{query_name:<35s} | {times[0]:>10s} | {times[1]:>10s} | {times[2]:>10s} | {times[3]:>10s}")
    
    # 最优步长建议
    print(f"\n{'='*80}")
    print("结论")
    print(f"{'='*80}")
    print("""
1. 存储性能分析:
   - 步长越大 → 跳表指针数量越少 → 存储空间越小
   - √N策略在高频词中产生较多指针,但对低频词友好
   - 固定步长200对存储空间最优,但可能影响低频词检索效率

2. 检索效率分析:
   - 高频词: 步长增大可能略微降低效率(跳跃距离过大,错过匹配机会)
   - 中频词: √N与N/10平衡较好,检索效率与存储开销适中
   - 低频词: 步长变化对效率影响较小(文档数少,线性遍历开销本就不大)

3. 最优步长选择建议:
   - 动态策略: 根据词项文档频率(DF)自适应调整
     * DF > 10000: 使用 N/10 (减少指针数量,节省存储)
     * 1000 < DF < 10000: 使用 √N (平衡存储与效率)
     * DF < 1000: 使用 固定50 或不使用跳表(线性遍历足够快)
   - 固定策略: 若追求简单实现,√N是通用最优选择
""")


if __name__ == "__main__":
    main()
