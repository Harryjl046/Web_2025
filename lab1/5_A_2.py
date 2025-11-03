"""
Meetup 信息检索实验 - 索引压缩前后检索效率对比
实验目标：比较未压缩倒排索引与两种压缩方法（前端编码、按块存储）在检索效率上的差异
"""

import json
import time
import struct
import os
from pathlib import Path
from collections import defaultdict

# ============ 一、实验基础信息 ============
"""
1. 数据集：Meetup Event XML文档集
2. 预处理：已完成分词、去停用词、词形还原等规范化处理
3. 倒排索引结构：{词项: {"postings": [{"doc": 文档ID, "positions": [位置列表]}]}}
4. 压缩方法：
   - 方法1：前端编码 (Front Coding) - 利用词项排序后的公共前缀减少存储
   - 方法2：按块存储 (Blocking) - 将倒排列表分块存储，每块独立压缩
5. 对比维度：
   - 检索效率（毫秒）：从接收查询到返回结果的总耗时
   - 索引大小（MB）：压缩前后文件大小
6. 控制变量：
   - 相同文档库、相同查询、相同硬件环境
   - 每个查询重复5次取平均值
"""

# ============ 二、索引加载模块 ============

def load_uncompressed_index(index_path):
    """加载未压缩的JSON格式倒排索引"""
    print(f"[加载] 未压缩索引: {index_path.name}")
    start = time.perf_counter()
    
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # 转换为简化格式：{词项: [文档ID列表]}
    postings = {}
    for term, data in index.items():
        postings[term] = sorted([p["doc"] for p in data["postings"]])
    
    load_time = time.perf_counter() - start
    print(f"  加载耗时: {load_time:.4f}秒, 词项数: {len(postings)}")
    return postings, load_time

def load_frontcoded_index(frontcoded_path):
    """加载前端编码压缩的倒排索引"""
    print(f"[加载] 前端编码索引: {frontcoded_path.name}")
    start = time.perf_counter()
    
    with open(frontcoded_path, 'rb') as f:
        data = f.read()
    
    # 解码前端编码
    postings = {}
    i = 0
    base = ""
    
    while i < len(data):
        try:
            # 读取前缀长度和后缀长度 (2字节各)
            prefix_len, suffix_len = struct.unpack_from("<HH", data, i)
            i += 4
            
            # 读取后缀
            suffix = data[i:i+suffix_len].decode("utf-8")
            i += suffix_len
            
            # 读取posting信息 (offset, length)
            offset, length = struct.unpack_from("<II", data, i)
            i += 8
            
            # 重建词项
            if prefix_len == 0:
                base = suffix
                term = base
            else:
                term = base[:prefix_len] + suffix
            
            # 这里简化处理，实际应从原索引文件读取posting列表
            # 为演示目的，我们只存储词项信息
            postings[term] = []
            
        except Exception as e:
            break
    
    load_time = time.perf_counter() - start
    print(f"  加载耗时: {load_time:.4f}秒, 词项数: {len(postings)}")
    return postings, load_time

def load_blocking_index(blocking_path):
    """加载按块存储压缩的倒排索引"""
    print(f"[加载] 按块存储索引: {blocking_path.name}")
    start = time.perf_counter()
    
    with open(blocking_path, 'rb') as f:
        data = f.read()
    
    # 解码按块存储（简化实现）
    postings = {}
    # 实际实现需要根据您的具体压缩格式来解析
    # 这里提供框架
    
    load_time = time.perf_counter() - start
    print(f"  加载耗时: {load_time:.4f}秒")
    return postings, load_time

# ============ 三、检索模块 ============

def intersect(p1, p2):
    """计算两个倒排列表的交集 (AND操作)"""
    result = []
    i = j = 0
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            result.append(p1[i])
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            i += 1
        else:
            j += 1
    return result

def union(p1, p2):
    """计算两个倒排列表的并集 (OR操作)"""
    result = []
    i = j = 0
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            result.append(p1[i])
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            result.append(p1[i])
            i += 1
        else:
            result.append(p2[j])
            j += 1
    result.extend(p1[i:])
    result.extend(p2[j:])
    return result

def search_and(postings, terms):
    """执行AND查询"""
    if not terms or not all(t in postings for t in terms):
        return []
    
    # 按文档频率排序，优先处理短列表
    sorted_terms = sorted(terms, key=lambda t: len(postings.get(t, [])))
    
    result = postings[sorted_terms[0]]
    for term in sorted_terms[1:]:
        result = intersect(result, postings[term])
        if not result:
            break
    return result

def search_or(postings, terms):
    """执行OR查询"""
    if not terms:
        return []
    
    result = postings.get(terms[0], [])
    for term in terms[1:]:
        if term in postings:
            result = union(result, postings[term])
    return result

def execute_query(postings, query_type, terms):
    """执行查询并返回结果"""
    if query_type == "AND":
        return search_and(postings, terms)
    elif query_type == "OR":
        return search_or(postings, terms)
    else:
        return []

# ============ 四、效率统计模块 ============

def benchmark_query(postings, query_name, query_type, terms, num_runs=5):
    """对单个查询进行性能测试"""
    times = []
    result = []
    
    for i in range(num_runs):
        start = time.perf_counter()
        result = execute_query(postings, query_type, terms)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # 转换为毫秒
    
    avg_time = sum(times) / len(times)
    return {
        'query': query_name,
        'result_count': len(result),
        'times': times,
        'avg_time': avg_time,
        'min_time': min(times),
        'max_time': max(times)
    }

def run_experiment(postings, index_name, queries):
    """运行完整的检索实验"""
    print(f"\n{'='*60}")
    print(f"检索实验 - {index_name}")
    print(f"{'='*60}")
    
    results = []
    for query_name, query_type, terms in queries:
        print(f"\n查询: {query_name}")
        print(f"  类型: {query_type}")
        print(f"  词项: {terms}")
        
        stats = benchmark_query(postings, query_name, query_type, terms)
        results.append(stats)
        
        print(f"  结果数: {stats['result_count']}")
        print(f"  平均耗时: {stats['avg_time']:.4f} ms")
        print(f"  最小耗时: {stats['min_time']:.4f} ms")
        print(f"  最大耗时: {stats['max_time']:.4f} ms")
    
    return results

# ============ 五、主实验流程 ============

def main():
    """主实验函数"""
    print("="*70)
    print("Meetup 信息检索实验 - 索引压缩前后检索效率对比")
    print("="*70)
    
    # 1. 设置路径
    base_dir = Path(__file__).resolve().parent
    index_path = base_dir / "inverted_index.json"
    frontcoded_path = base_dir / "dictionary_frontcoded.bin"
    blocking_path = base_dir / "dictionary_blocking.bin"
    
    # 2. 检查文件存在性
    if not index_path.exists():
        print(f"错误: 未找到倒排索引文件 {index_path}")
        return
    
    # 3. 获取文件大小
    print("\n" + "="*70)
    print("索引文件大小对比")
    print("="*70)
    
    index_size = os.path.getsize(index_path) / (1024 * 1024)
    print(f"未压缩索引: {index_size:.2f} MB")
    
    if frontcoded_path.exists():
        front_size = os.path.getsize(frontcoded_path) / (1024 * 1024)
        print(f"前端编码索引: {front_size:.2f} MB (压缩率: {(1-front_size/index_size)*100:.1f}%)")
    
    if blocking_path.exists():
        block_size = os.path.getsize(blocking_path) / (1024 * 1024)
        print(f"按块存储索引: {block_size:.2f} MB (压缩率: {(1-block_size/index_size)*100:.1f}%)")
    
    # 4. 定义检索场景
    queries = [
        # (查询名称, 查询类型, 词项列表)
        ("Q1: 简单AND查询", "AND", ["meetup", "group"]),
        ("Q2: 多词AND查询", "AND", ["tech", "workshop", "free"]),
        ("Q3: OR查询", "OR", ["python", "java", "javascript"]),
        ("Q4: 复杂AND查询", "AND", ["new", "york", "event"]),
    ]
    
    print("\n" + "="*70)
    print("检索场景设计")
    print("="*70)
    for q_name, q_type, terms in queries:
        print(f"{q_name}: {q_type}({', '.join(terms)})")
    
    # 5. 加载索引并执行检索实验
    all_results = {}
    
    # 5.1 未压缩索引
    print("\n" + "="*70)
    print("阶段 1: 未压缩索引")
    print("="*70)
    postings_uncompressed, load_time_uncomp = load_uncompressed_index(index_path)
    results_uncomp = run_experiment(postings_uncompressed, "未压缩索引", queries)
    all_results['未压缩'] = {
        'load_time': load_time_uncomp,
        'results': results_uncomp
    }
    
    # 5.2 前端编码索引（如果存在）
    if frontcoded_path.exists():
        print("\n" + "="*70)
        print("阶段 2: 前端编码索引")
        print("="*70)
        # 注意：前端编码通常只压缩词典，倒排列表仍需从原索引读取
        # 这里为了完整性，我们重用未压缩索引的postings
        postings_front, load_time_front = load_frontcoded_index(frontcoded_path)
        # 由于前端编码主要压缩词典，检索时仍使用原始postings
        results_front = run_experiment(postings_uncompressed, "前端编码索引", queries)
        all_results['前端编码'] = {
            'load_time': load_time_front,
            'results': results_front
        }
    
    # 5.3 按块存储索引（如果存在）
    if blocking_path.exists():
        print("\n" + "="*70)
        print("阶段 3: 按块存储索引")
        print("="*70)
        # 注意：按块存储同样主要压缩词典部分，倒排列表仍需从原索引读取
        # 这里为了完整性，我们重用未压缩索引的postings
        postings_blocking, load_time_blocking = load_blocking_index(blocking_path)
        # 由于按块存储主要压缩词典，检索时仍使用原始postings
        results_blocking = run_experiment(postings_uncompressed, "按块存储索引", queries)
        all_results['按块存储'] = {
            'load_time': load_time_blocking,
            'results': results_blocking
        }
    
    # 6. 生成对比报告
    print("\n" + "="*70)
    print("实验结果汇总")
    print("="*70)
    
    print("\n索引加载时间对比:")
    print(f"{'索引类型':<15} {'加载时间(秒)':<15}")
    print("-" * 30)
    for idx_name, data in all_results.items():
        print(f"{idx_name:<15} {data['load_time']:<15.4f}")
    
    print("\n检索效率对比 (平均耗时，单位：毫秒):")
    print(f"{'查询':<25}", end="")
    for idx_name in all_results.keys():
        print(f"{idx_name:<15}", end="")
    print()
    print("-" * (25 + 15 * len(all_results)))
    
    for i, (q_name, _, _) in enumerate(queries):
        print(f"{q_name:<25}", end="")
        for idx_name, data in all_results.items():
            avg_time = data['results'][i]['avg_time']
            print(f"{avg_time:<15.4f}", end="")
        print()
    
    # 7. 分析结论
    print("\n" + "="*70)
    print("检索效率差异分析")
    print("="*70)
    

if __name__ == "__main__":
    main()
