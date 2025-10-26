import os
import json
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict
from tqdm import tqdm

def build_skip_pointers(posting_list):
    n = len(posting_list)
    skip_interval = int(n ** 0.5)
    skips = []
    if skip_interval > 1:
        for i in range(0, n, skip_interval):
            next_i = i + skip_interval
            if next_i < n:
                skips.append({
                    "from": posting_list[i],
                    "to": posting_list[next_i],
                    "jump": skip_interval
                })
    return skips

def build_inverted_index(tokenized_dir):
    """构建倒排表的函数"""
    inverted_index = defaultdict(lambda: defaultdict(list))
    files=[f for f in os.listdir(tokenized_dir) if f.endswith(".txt")]
    print("正在读取文件...")
    for filename in tqdm(files,desc="处理文件",unit="file"):        
        file_path = tokenized_dir / filename
        with open(file_path, "r", encoding="utf-8") as f:
            words = f.read().split()
            for pos,w in enumerate(words):  
                inverted_index[w][filename].append(pos)
    print("正在生成倒排表...")
    index_with_skips = {}
    for term, doc_dict  in tqdm(inverted_index.items(),desc="生成倒排表",unit="term"):
        sorted_docs = sorted(doc_dict.keys())  # 保证有序
        skips = build_skip_pointers(sorted_docs)
        index_with_skips[term] = {
            "postings": [
                {"doc":doc,"positions":doc_dict[doc]}for doc in sorted_docs
            ],
            "skips": skips
        }
    print("正在排序...")
    sorted_inverted_index = {term: index_with_skips[term] for term in sorted(index_with_skips.keys())}
    return sorted_inverted_index

def build_dictionary(inverted_index_path,dictionary_path):
    """根据倒排表文件生成词典"""
    with open(inverted_index_path, "r", encoding="utf-8") as f:
        inverted_index = json.load(f)

    sorted_terms = sorted(inverted_index.keys())
    dictionary = {}
    offset = 0

    for term in tqdm(sorted_terms, desc="构建词典", unit="term"):
        posting_data = inverted_index[term]
        posting_str = json.dumps(posting_data, ensure_ascii=False)
        posting_bytes = posting_str.encode('utf-8')
        length = len(posting_bytes)

        dictionary[term]={
            "offset":offset,
            "length":length
        }
        offset += length

    with open(dictionary_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)

    print(f"📖 词典已生成，共 {len(dictionary)} 个词项")
    print(f"📄 保存路径：{dictionary_path}")   

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parents[2]
    tokenized_dir = BASE_DIR / "Lab1/tokenized"
    inverted_index_path = BASE_DIR /  "Lab1/inverted_index.json"
    dictionary_path = BASE_DIR /  "Lab1/dictionary.json"

    print("正在构建倒排表...")
    inverted_index=build_inverted_index(tokenized_dir)

    with open(inverted_index_path, "w", encoding="utf-8") as f:
        json.dump(inverted_index, f, indent=2, ensure_ascii=False)

    print(f"✅  倒排表已生成，共 {len(inverted_index)} 个词项")
    print(f"📄 保存路径：{inverted_index_path}")

    build_dictionary(inverted_index_path,dictionary_path)
