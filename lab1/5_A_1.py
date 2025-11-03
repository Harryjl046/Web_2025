import time
import json
from pathlib import Path
from collections import defaultdict

# --- 数据加载 ---
def load_postings(inverted_index_path):
    """从真实的倒排索引文件加载数据"""
    print(f"正在从 '{inverted_index_path.name}' 加载倒排索引...")
    with open(inverted_index_path, "r", encoding="utf-8") as f:
        inv = json.load(f)
    
    postings = defaultdict(list)
    for term, data in inv.items():
        # 提取每个词项的倒排列表（仅文档ID），并确保其有序
        postings[term] = sorted([p["doc"] for p in data["postings"]])
    
    print(f"加载完成，共 {len(postings)} 个词项。")
    return postings

# --- 核心布尔运算函数 ---
def intersect(p1, p2):
    """计算两个倒排列表的交集 (AND)"""
    answer = []
    i = j = 0
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            answer.append(p1[i])
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            i += 1
        else:
            j += 1
    return answer

def union(p1, p2):
    """计算两个倒排列表的并集 (OR)"""
    answer = []
    i = j = 0
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            answer.append(p1[i])
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            answer.append(p1[i])
            i += 1
        else:
            answer.append(p2[j])
            j += 1
    answer.extend(p1[i:])
    answer.extend(p2[j:])
    return answer

def difference(p1, p2):
    """计算两个倒排列表的差集 (p1 AND NOT p2)"""
    answer = []
    i = j = 0
    while i < len(p1) and j < len(p2):
        if p1[i] == p2[j]:
            i += 1
            j += 1
        elif p1[i] < p2[j]:
            answer.append(p1[i])
            i += 1
        else:
            j += 1
    answer.extend(p1[i:])
    return answer

# --- 实验执行框架 ---
def run_query(query_func, postings, num_runs=10):
    """重复运行一个查询函数并返回平均耗时，以减少偶然误差"""
    total_time = 0
    result = []
    for i in range(num_runs):
        start_time = time.perf_counter()
        result = query_func(postings)
        end_time = time.perf_counter()
        total_time += (end_time - start_time)
        # 第一次运行时打印结果大小
        if i == 0:
            print(f"    -> 结果集大小: {len(result)}")
    return total_time / num_runs

# --- 查询 Q1: new AND york AND event AND meetup AND group ---
def q1_strategy1(postings): # 低频优先策略：按DF从小到大顺序处理
    # 动态获取词项列表并按文档频率（列表长度）排序
    terms = ['new', 'york', 'event', 'meetup', 'group']
    sorted_terms = sorted(terms, key=lambda t: len(postings[t]))
    
    # 从最短的列表开始，依次进行交集运算
    result = postings[sorted_terms[0]]
    for term in sorted_terms[1:]:
        result = intersect(result, postings[term])
    return result

def q1_strategy2(postings): # 高频优先策略：按DF从大到小顺序处理（低效）
    # 动态获取词项列表并按文档频率（列表长度）逆序排序
    terms = ['new', 'york', 'event', 'meetup', 'group']
    sorted_terms = sorted(terms, key=lambda t: len(postings[t]), reverse=True)
    
    # 从最长的列表开始，依次进行交集运算
    result = postings[sorted_terms[0]]
    for term in sorted_terms[1:]:
        result = intersect(result, postings[term])
    return result

# --- 查询 Q2: free AND (social OR hiking OR party) AND NOT online ---
def q2_strategy1(postings): # 低频优先 (分配律)
    # 动态获取 OR 分支词项并按 DF 排序
    or_terms = ['social', 'hiking', 'party']
    # 对每个 OR 词项与 free 进行 AND，生成中间结果
    and_results = []
    for term in or_terms:
        and_results.append(intersect(postings['free'], postings[term]))
    
    # 将所有中间结果进行 OR 合并
    result = and_results[0]
    for and_res in and_results[1:]:
        result = union(result, and_res)
    
    # 最后排除 online
    return difference(result, postings['online'])

def q2_strategy2(postings): # 先OR后AND
    # 先将所有 OR 词项合并
    or_terms = ['social', 'hiking', 'party']
    res_or = postings[or_terms[0]]
    for term in or_terms[1:]:
        res_or = union(res_or, postings[term])
    
    # 再与 free 进行 AND
    res_and = intersect(postings['free'], res_or)
    
    # 最后排除 online
    return difference(res_and, postings['online'])

# --- 查询 Q3: (career OR leadership) AND workshop AND NOT agile ---
def q3_strategy1(postings): # 后NOT策略：先完成所有AND/OR运算，最后排除NOT
    # 1. 先合并 OR 词项
    or_terms = ['career', 'leadership']
    res_or = postings[or_terms[0]]
    for term in or_terms[1:]:
        res_or = union(res_or, postings[term])
    
    # 2. 与 workshop 进行 AND
    res_and = intersect(res_or, postings['workshop'])
    
    # 3. 最后排除 agile (后NOT)
    return difference(res_and, postings['agile'])

def q3_strategy2(postings): # 先NOT策略：提前从workshop中排除agile，再进行其他运算
    # 1. 先从 workshop 中排除 agile (先NOT)
    res_not = difference(postings['workshop'], postings['agile'])
    
    # 2. 合并 OR 词项
    or_terms = ['career', 'leadership']
    res_or = postings[or_terms[0]]
    for term in or_terms[1:]:
        res_or = union(res_or, postings[term])
    
    # 3. 与处理过NOT的workshop进行 AND
    return intersect(res_or, res_not)

def analyze_and_run(postings):
    """定义查询、检查词项、运行实验并打印结果"""
    queries = {
        "Q1": {
            "expr": "new AND york AND event AND meetup AND group",
            "terms": ['new', 'york', 'event', 'meetup', 'group'],
            "strategies": {"低频优先": q1_strategy1, "高频优先": q1_strategy2}
        },
        "Q2": {
            "expr": "free AND (social OR hiking OR party) AND NOT online",
            "terms": ['free', 'social', 'hiking', 'party', 'online'],
            "strategies": {"先AND后OR": q2_strategy1, "先OR后AND": q2_strategy2}
        },
        "Q3": {
            "expr": "(career OR leadership) AND workshop AND NOT agile",
            "terms": ['career', 'leadership', 'workshop', 'agile'],
            "strategies": {"后NOT": q3_strategy1, "先NOT": q3_strategy2}
        }
    }

    for name, cfg in queries.items():
        print(f"\n--- 查询 {name}: {cfg['expr']} ---")
        
        # 检查词项是否存在并打印其文档频率
        print("  词项文档频率 (DF) [按频率从低到高排序]:")
        all_terms_found = True
        term_dfs = {}
        for term in cfg['terms']:
            if term in postings:
                term_dfs[term] = len(postings[term])
            else:
                print(f"    - {term}: 未在索引中找到!")
                all_terms_found = False
        
        # 按文档频率从小到大排序后打印
        for term in sorted(term_dfs.keys(), key=lambda t: term_dfs[t]):
            print(f"    - {term}: {term_dfs[term]}")
        
        if not all_terms_found:
            print("  -> 由于缺少部分词项，跳过此查询的实验。")
            continue

        # 运行不同策略并记录时间
        print("  策略性能对比:")
        for strategy_name, strategy_func in cfg['strategies'].items():
            print(f"  - 策略: {strategy_name}")
            avg_time = run_query(strategy_func, postings)
            print(f"    -> 平均耗时: {avg_time:.6f} 秒")

# --- 主函数 ---
if __name__ == "__main__":
    # 确保 inverted_index.json 文件与此脚本在同一目录下
    base_dir = Path(__file__).resolve().parent
    inverted_index_path = base_dir / "inverted_index.json"

    if not inverted_index_path.exists():
        print(f"错误: 倒排索引文件 '{inverted_index_path}' 未找到。")
        print("请确保 'inverted_index.json' 与 '5_A_1.py' 在同一个文件夹中。")
    else:
        # 1. 加载真实倒排索引
        real_postings = load_postings(inverted_index_path)
        
        # 2. 运行实验
        analyze_and_run(real_postings)
