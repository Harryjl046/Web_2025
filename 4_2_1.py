import json
import struct
import os
from pathlib import Path

def common_prefix_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if x == y:
            n += 1
        else:
            break
    return n

def front_coding_binary(in_path, out_path, block_size=4):
    with open(in_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    terms = sorted(d.keys())

    with open(out_path, "wb") as f:
        i = 0
        while i < len(terms):
            block = terms[i:i+block_size]
            base = block[0]

            # --- 写入block头（首词）---
            base_bytes = base.encode("utf-8")
            f.write(struct.pack("B", 0))                      # prefix_len = 0
            f.write(struct.pack("B", len(base_bytes)))         # suffix_len
            f.write(base_bytes)                                # suffix内容
            f.write(struct.pack("<II", d[base]["offset"], d[base]["length"]))  # offset+length

            # --- 后续词 ---
            for term in block[1:]:
                prefix = common_prefix_len(base, term)
                suffix = term[prefix:].encode("utf-8")
                f.write(struct.pack("B", prefix))              # 前缀长度
                f.write(struct.pack("B", len(suffix)))         # 后缀长度
                f.write(suffix)
                f.write(struct.pack("<II", d[term]["offset"], d[term]["length"]))
            i += block_size

# 示例调用
# front_coding_binary("dictionary.json", "dictionary_frontcoded.bin", block_size=3)

def front_coding_decode(path, block_size=4):
    """解码前端编码函数"""
    result = []
    with open(path, "rb") as f:
        data = f.read()
    i = 0
    base = ""
    while i < len(data):
        prefix_len = data[i]; i += 1
        suffix_len = data[i]; i += 1
        suffix = data[i:i+suffix_len].decode("utf-8"); i += suffix_len
        offset, length = struct.unpack_from("<II", data, i); i += 8
        if prefix_len == 0:
            base = suffix
            term = base
        else:
            term = base[:prefix_len] + suffix
        result.append((term, offset, length))
    return result
#前端编码的示例代码
BASE_DIR = Path(__file__).resolve().parents[1]
dictionary_path = BASE_DIR /  "dictionary.json"
frontedcoded_path = BASE_DIR /  "dictionary_frontcoded.bin"

front_coding_binary(dictionary_path,frontedcoded_path, block_size=4)
result=front_coding_decode(frontedcoded_path, block_size=4)
print(result[:3])

