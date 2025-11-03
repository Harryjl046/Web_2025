"""
分析倒排索引中的词项文档频率分布
找出高频/中频/低频词项用于跳表实验
"""

import json
import time
from pathlib import Path
from collections import Counter

def analyze_term_frequencies(index_path):
    """分析词项文档频率"""
    print("[加载] 倒排索引...")
    start = time.perf_counter()
    
    with open(index_path, 'r', encoding='utf-8') as f:
        inv_index = json.load(f)
    
    load_time = time.perf_counter() - start
    print(f"  加载耗时: {load_time:.4f}秒")
    print(f"  词项总数: {len(inv_index)}\n")
    
    # 统计每个词项的文档频率
    term_frequencies = {}
    for term, data in inv_index.items():
        df = len(data["postings"])
        term_frequencies[term] = df
    
    # 排序
    sorted_terms = sorted(term_frequencies.items(), key=lambda x: x[1], reverse=True)
    
    # 统计频率分布
    print("[文档频率分布统计]")
    freq_ranges = [
        (10000, float('inf'), "超高频"),
        (5000, 10000, "高频"),
        (1000, 5000, "中高频"),
        (500, 1000, "中频"),
        (100, 500, "中低频"),
        (10, 100, "低频"),
        (1, 10, "超低频")
    ]
    
    for min_f, max_f, label in freq_ranges:
        count = sum(1 for _, df in term_frequencies.items() if min_f <= df < max_f)
        print(f"  {label:8s}: {count:6d} 词项 (DF范围: {min_f}-{max_f if max_f != float('inf') else '∞'})")
    
    # 展示Top 30高频词
    print(f"\n[Top 30 高频词项]")
    print(f"{'排名':<6s} {'词项':<25s} {'文档频率(DF)':<15s}")
    print("-" * 50)
    for i, (term, df) in enumerate(sorted_terms[:30], 1):
        print(f"{i:<6d} {term:<25s} {df:<15d}")
    
    # 展示中频词样本
    mid_freq_terms = [(t, df) for t, df in sorted_terms if 500 <= df <= 2000]
    print(f"\n[中频词项样本 (DF: 500-2000)]")
    print(f"{'词项':<25s} {'文档频率(DF)':<15s}")
    print("-" * 45)
    for term, df in mid_freq_terms[:20]:
        print(f"{term:<25s} {df:<15d}")
    
    # 展示低频词样本
    low_freq_terms = [(t, df) for t, df in sorted_terms if 50 <= df <= 200]
    print(f"\n[低频词项样本 (DF: 50-200)]")
    print(f"{'词项':<25s} {'文档频率(DF)':<15s}")
    print("-" * 45)
    for term, df in low_freq_terms[:20]:
        print(f"{term:<25s} {df:<15d}")
    
    # 推荐查询组合
    print(f"\n{'='*60}")
    print("推荐用于跳表实验的查询组合")
    print(f"{'='*60}")
    
    # 高频组合 (DF > 5000)
    high_freq = [(t, df) for t, df in sorted_terms if df > 5000][:10]
    print(f"\n[高频词项组合建议] (DF > 5000)")
    if len(high_freq) >= 2:
        for i in range(0, min(6, len(high_freq)-1), 2):
            t1, df1 = high_freq[i]
            t2, df2 = high_freq[i+1]
            print(f"  {t1} (DF={df1}) AND {t2} (DF={df2})")
    
    # 中频组合 (500 < DF < 2000)
    print(f"\n[中频词项组合建议] (500 < DF < 2000)")
    if len(mid_freq_terms) >= 2:
        for i in range(0, min(6, len(mid_freq_terms)-1), 2):
            t1, df1 = mid_freq_terms[i]
            t2, df2 = mid_freq_terms[i+1]
            print(f"  {t1} (DF={df1}) AND {t2} (DF={df2})")
    
    # 低频组合 (50 < DF < 200)
    print(f"\n[低频词项组合建议] (50 < DF < 200)")
    if len(low_freq_terms) >= 2:
        for i in range(0, min(6, len(low_freq_terms)-1), 2):
            t1, df1 = low_freq_terms[i]
            t2, df2 = low_freq_terms[i+1]
            print(f"  {t1} (DF={df1}) AND {t2} (DF={df2})")

if __name__ == "__main__":
    base_path = Path(__file__).parent
    index_path = base_path / "inverted_index.json"
    
    if not index_path.exists():
        print(f"错误: 找不到倒排索引文件 {index_path}")
    else:
        analyze_term_frequencies(index_path)
