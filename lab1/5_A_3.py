"""
Meetup 信息检索实验 - 短语检索与词项位置信息的影响分析
对比不利用位置信息与利用位置信息两种检索策略的效果差异
"""

import json
import time
from pathlib import Path
from collections import defaultdict

def load_inverted_index(index_path):
    """加载倒排索引（包含位置信息）"""
    print(f"[加载] 倒排索引: {index_path.name}")
    start = time.perf_counter()
    
    with open(index_path, 'r', encoding='utf-8') as f:
        inv_index = json.load(f)
    
    # 格式: {词项: {文档ID: [位置列表]}}
    index = {}
    for term, data in inv_index.items():
        index[term] = {}
        for posting in data["postings"]:
            doc_id = posting["doc"]
            positions = posting.get("positions", [])
            index[term][doc_id] = sorted(positions)
    
    load_time = time.perf_counter() - start
    print(f"  词项数: {len(index)}, 耗时: {load_time:.4f}秒\n")
    return index

def search_without_positions(index, phrase_terms):
    """方法1：不利用位置信息，只做词项AND查询（会产生误匹配）"""
    if not phrase_terms or not all(term in index for term in phrase_terms):
        return []
    
    # 计算所有词项的文档交集
    sorted_terms = sorted(phrase_terms, key=lambda t: len(index[t]))
    result = set(index[sorted_terms[0]].keys())
    for term in sorted_terms[1:]:
        result = result.intersection(set(index[term].keys()))
        if not result:
            break
    
    return sorted(list(result))

def verify_phrase_positions(positions_list):
    """验证词项位置是否连续（position[i+1] = position[i] + 1）"""
    if not positions_list or len(positions_list) < 2:
        return []
    
    valid_positions = []
    for start_pos in positions_list[0]:
        is_valid = True
        for i in range(1, len(positions_list)):
            expected_pos = start_pos + i
            if expected_pos not in positions_list[i]:
                is_valid = False
                break
        if is_valid:
            valid_positions.append(start_pos)
    
    return valid_positions

def search_with_positions(index, phrase_terms):
    """方法2：利用位置信息，精确匹配短语（无误匹配）"""
    if not phrase_terms or not all(term in index for term in phrase_terms):
        return {}
    
    # 找到包含所有词项的文档
    doc_sets = [set(index[term].keys()) for term in phrase_terms]
    candidate_docs = set.intersection(*doc_sets)
    
    # 验证词项位置是否连续
    phrase_results = {}
    for doc_id in candidate_docs:
        positions_list = [index[term][doc_id] for term in phrase_terms]
        valid_positions = verify_phrase_positions(positions_list)
        if valid_positions:
            phrase_results[doc_id] = valid_positions
    
    return phrase_results

def run_phrase_search_experiment(index, phrase_name, phrase_terms, num_runs=5):
    """执行短语检索实验并对比两种方法"""
    print(f"\n{'='*70}")
    print(f"短语检索: {phrase_name} - {' '.join(phrase_terms)}")
    print(f"{'='*70}")
    
    # 方法1：不利用位置信息
    print("\n[方法1] 不利用位置信息（只做AND查询）")
    
    times_basic = []
    for _ in range(num_runs):
        start = time.perf_counter()
        results_basic = search_without_positions(index, phrase_terms)
        end = time.perf_counter()
        times_basic.append((end - start) * 1000)  # 转换为毫秒
    
    avg_time_basic = sum(times_basic) / len(times_basic)
    print(f"  结果: {len(results_basic)} 个文档（可能误匹配）")
    print(f"  耗时: {avg_time_basic:.4f} 毫秒")
    
    # 方法2：利用位置信息
    print("\n[方法2] 利用位置信息（精确匹配短语）")
    
    times_extended = []
    for _ in range(num_runs):
        start = time.perf_counter()
        results_extended = search_with_positions(index, phrase_terms)
        end = time.perf_counter()
        times_extended.append((end - start) * 1000)
    
    avg_time_extended = sum(times_extended) / len(times_extended)
    total_phrase_occurrences = sum(len(positions) for positions in results_extended.values())
    
    print(f"  结果: {len(results_extended)} 个文档（精确匹配）")
    print(f"  短语出现: {total_phrase_occurrences} 次")
    print(f"  耗时: {avg_time_extended:.4f} 毫秒")
    
    # 效果对比
    print("\n[对比分析]")
    false_positives = len(results_basic) - len(results_extended)
    if false_positives > 0:
        print(f"  误匹配: {false_positives} 个 ({false_positives/len(results_basic)*100:.1f}%)")
    
    efficiency_diff = avg_time_extended - avg_time_basic
    print(f"  耗时差异: {'+' if efficiency_diff > 0 else ''}{efficiency_diff:.4f} 毫秒 ({efficiency_diff/avg_time_basic*100:+.1f}%)")
    
    if results_extended and len(results_extended) <= 5:
        print(f"\n  精确匹配示例:")
        for doc_id, positions in results_extended.items():
            print(f"    文档 {doc_id}: 位置 {positions}")
    
    return {
        'phrase': phrase_name,
        'terms': phrase_terms,
        'basic_count': len(results_basic),
        'extended_count': len(results_extended),
        'false_positives': false_positives,
        'avg_time_basic': avg_time_basic,
        'avg_time_extended': avg_time_extended,
        'phrase_occurrences': total_phrase_occurrences
    }

# ============ 七、主实验流程 ============

def main():
    """主实验函数"""
    print("="*70)
    print("Meetup 短语检索实验 - 词项位置信息对检索效果的影响")
    print("="*70)
    
    # 1. 设置路径
    base_dir = Path(__file__).resolve().parent
    index_path = base_dir / "inverted_index.json"
    
    if not index_path.exists():
        print(f"错误: 未找到倒排索引文件 {index_path}")
        return
    
    # 2. 加载倒排索引（包含位置信息）
    index = load_inverted_index(index_path)
    
    # 3. 定义短语检索任务
    phrases = [
        ("场景1: heavy rain", ["heavy", "rain"]),
        ("场景2: new york", ["new", "york"]),
        ("场景3: beer tasting ", ["beer", "tasting"]),
    ]
    
    # 4. 执行实验
    all_results = []
    for phrase_name, phrase_terms in phrases:
        result = run_phrase_search_experiment(
            index, 
            phrase_name, 
            phrase_terms
        )
        all_results.append(result)
    
    # 5. 综合分析
    print("\n" + "="*70)
    print("综合分析与结论")
    print("="*70)
    
    print("\n1. 检索准确性对比表:")
    print(f"{'短语场景':<20} {'不利用位置':<15} {'利用位置':<15} {'误匹配率':<15}")
    print("-" * 65)
    for r in all_results:
        fp_rate = f"{r['false_positives']/r['basic_count']*100:.1f}%" if r['basic_count'] > 0 else "N/A"
        print(f"{r['phrase']:<20} {r['basic_count']:<15} {r['extended_count']:<15} {fp_rate:<15}")
    
    print("\n2. 检索效率对比表 (单位: 毫秒):")
    print(f"{'短语场景':<20} {'不利用位置':<15} {'利用位置':<15} {'耗时差异':<15}")
    print("-" * 65)
    for r in all_results:
        diff = r['avg_time_extended'] - r['avg_time_basic']
        diff_str = f"+{diff:.4f}" if diff > 0 else f"{diff:.4f}"
        print(f"{r['phrase']:<20} {r['avg_time_basic']:<15.4f} {r['avg_time_extended']:<15.4f} {diff_str:<15}")
    

if __name__ == "__main__":
    main()
