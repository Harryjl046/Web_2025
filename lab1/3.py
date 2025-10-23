import os
import json
from pathlib import Path
from collections import defaultdict
import tqdm as tqdm

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

    for filename in os.listdir(tokenized_dir):
        if filename.endswith(".txt"):
            file_path = tokenized_dir / filename
            with open(file_path, "r", encoding="utf-8") as f:
                words = f.read().split()
                for pos,w in enumerate(words):  
                    inverted_index[w][filename].append(pos)

    index_with_skips = {}
    for term, doc_dict  in inverted_index.items():
        sorted_docs = sorted(doc_dict.keys())  # 保证有序
        skips = build_skip_pointers(sorted_docs)
        index_with_skips[term] = {
            "postings": [
                {"doc":doc,"positions":doc_dict[doc]}for doc in sorted_docs
            ],
            "skips": skips
        }
    return index_with_skips

def build_dictionary(inverted_index_path,dictionary_path):
    """根据倒排表文件生成词典"""
    with open(inverted_index_path, "r", encoding="utf-8") as f:
        inverted_index = json.load(f)

    sorted_terms = sorted(inverted_index.keys())
    dictionary = {}
    offset = 0

    for term in sorted_terms:
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

    BASE_DIR = Path(__file__).resolve().parents[1]
    tokenized_dir = BASE_DIR / "tokenized"
    inverted_index_path = BASE_DIR /  "inverted_index.json"
    dictionary_path = BASE_DIR /  "dictionary.json"

    print("正在构建倒排表...")
    inverted_index=build_inverted_index(tokenized_dir)

    with open(inverted_index_path, "w", encoding="utf-8") as f:
        json.dump(inverted_index, f, indent=2, ensure_ascii=False)

    print(f"✅ 倒排表已生成，共 {len(inverted_index)} 个词项")
    print(f"📄 保存路径：{inverted_index_path}")

    build_dictionary(inverted_index_path,dictionary_path)
