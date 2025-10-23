import json
import struct
import io
from typing import Optional, Tuple, List
from pathlib import Path

def blocking_compressed(in_path,out_path,block_size=4):

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    terms = sorted(data.keys())  # 按键排序
    grouped = {}

    for i in range(0, len(terms), block_size):
        group_terms = terms[i:i+4]
        if not group_terms:
            continue

        first_term = group_terms[0]
        group_name = f"group_{i//4 + 1}"

        offset = data[first_term]["offset"]
        lengths = [data[t]["length"] for t in group_terms[:3]]

        grouped[group_name] = {
            "terms": group_terms,
            "offset": offset,
            "lengths": lengths
        }

    with open(out_path, "wb") as fbin:
        for group_name, group in grouped.items():
            terms = group["terms"]
            offset = group["offset"]
            lengths = group["lengths"]

            # --- 构造组内二进制数据 ---
            buf = io.BytesIO()

            # 写入4个term（不足补空字符串）
            for i in range(4):
                term = terms[i] if i < len(terms) else ""
                t_bytes = term.encode("utf-8")
                buf.write(struct.pack("<H", len(t_bytes)))  # 2字节长度
                buf.write(t_bytes)

            # 写入offset与3个lengths
            buf.write(struct.pack("<I", offset))
            for l in lengths:
                buf.write(struct.pack("<I", l))
            for _ in range(3 - len(lengths)):  # 不足补0
                buf.write(struct.pack("<I", 0))

            # --- 写入组长度和数据 ---
            chunk = buf.getvalue()
            fbin.write(struct.pack("<I", len(chunk)))  # 4字节长度头
            fbin.write(chunk)

    print("写入完成")

def blocking_decompressed(block_path):
    groups = []
    with open(block_path, "rb") as f:
        while True:
            header = f.read(4)
            if not header:
                break
            group_len = struct.unpack("<I", header)[0]
            group_data = f.read(group_len)
            buf = io.BytesIO(group_data)

            # 读取4个term
            terms = []
            for _ in range(4):
                len_bytes = buf.read(2)
                l = struct.unpack("<H", len_bytes)[0]
                t_bytes = buf.read(l)
                try:
                    term = t_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    term = t_bytes.decode("utf-8", errors="replace")
                terms.append(term)

            # 读取offset + 3 lengths
            offset = struct.unpack("<I", buf.read(4))[0]
            lengths = list(struct.unpack("<III", buf.read(12)))

            groups.append({
                "terms": terms,
                "offset": offset,
                "lengths": lengths
            })
    print("读取成功")
    return groups



if __name__=="__main__":

    BASE_DIR = Path(__file__).resolve().parents[1]
    dictionary_path = BASE_DIR /  "dictionary.json"
    block_path = BASE_DIR /  "dictionary_blocking.bin"

    blocking_compressed(dictionary_path,block_path)
    blocking_decompressed(block_path)
