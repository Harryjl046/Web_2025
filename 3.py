import os
import json
from pathlib import Path
from collections import defaultdict

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

# 设置路径
BASE_DIR = Path(__file__).resolve().parents[1]
tokenized_dir = BASE_DIR / "tokenized"
output_path = BASE_DIR /  "inverted_index.json"

# 倒排表字典，键为词项，值为包含该词的文档集合
inverted_index = defaultdict(set)

# 遍历分词后的文件
for filename in os.listdir(tokenized_dir):
    if filename.endswith(".txt"):
        file_path = os.path.join(tokenized_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            words = f.read().split()
            for w in set(words):  # 使用 set 去重，避免重复添加
                inverted_index[w].add(filename)

index_with_skips = {}
for term, docs in inverted_index.items():
    sorted_docs = sorted(docs)  # 保证有序
    skips = build_skip_pointers(sorted_docs)
    index_with_skips[term] = {
        "postings": sorted_docs,
        "skips": skips
    }

# 保存为 JSON 文件
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(index_with_skips, f, indent=2, ensure_ascii=False)

print(f"✅ 倒排表已生成，共 {len(inverted_index)} 个词项")
print(f"📄 保存路径：{output_path}")
