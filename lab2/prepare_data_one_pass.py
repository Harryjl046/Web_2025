import gzip
import os
import random
from collections import Counter

# ================= 配置参数 =================
SOURCE_FILE = 'data/freebase_douban.gz'  # 原始压缩文件路径
OUTPUT_DIR = 'data/freebase'       # 输出文件夹
MIN_ENTITY_FREQ = 10               # 实体最少出现次数（全量扫描时建议稍微调高，例如 20 或 50，以控制规模）
MIN_RELATION_FREQ = 10             # 关系最少出现次数
TARGET_ENTITY_COUNT = 6000         # 目标实体数量
MAX_RAW_TRIPLES = 2000000          # 内存中最大保留的原始三元组数量（用于单轮扫描）
# ===========================================

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

def load_and_filter_one_pass(filepath):
    """
    单轮扫描模式：
    1. 读取前 MAX_RAW_TRIPLES 条有效三元组到内存
    2. 在内存中统计频率
    3. 筛选 Top K 实体
    4. 过滤并返回最终三元组
    """
    print(f">>> 开始单轮扫描（限制读取前 {MAX_RAW_TRIPLES} 条有效数据）...")
    
    raw_triples = []
    entity_counter = Counter()
    relation_counter = Counter()
    
    try:
        with gzip.open(filepath, 'rb') as f:
            for i, line in enumerate(f):
                if i % 100000 == 0 and i > 0:
                    print(f"    已扫描 {i} 行 | 已收集 {len(raw_triples)} 条有效三元组...", end='\r')
                
                # 如果收集够了，直接停止读取
                if len(raw_triples) >= MAX_RAW_TRIPLES:
                    print(f"\n    已达到内存限制 ({MAX_RAW_TRIPLES} 条)，停止读取。")
                    break

                try:
                    line_str = line.strip().decode('utf-8')
                    parts = line_str.split('\t')
                    if len(parts) < 3: continue
                    
                    h, r, t = parts[0], parts[1], parts[2]
                    
                    # 基础前缀过滤
                    if not (h.startswith("<http://rdf.freebase.com/ns/") and 
                            t.startswith("<http://rdf.freebase.com/ns/")):
                        continue

                    # 去除前缀和后缀，只保留 ID
                    h = h.replace("<http://rdf.freebase.com/ns/", "").replace(">", "")
                    r = r.replace("<http://rdf.freebase.com/ns/", "").replace(">", "")
                    t = t.replace("<http://rdf.freebase.com/ns/", "").replace(">", "")
                    
                    # 存入内存列表
                    raw_triples.append((h, r, t))
                    
                    # 实时统计频率
                    entity_counter[h] += 1
                    entity_counter[t] += 1
                    relation_counter[r] += 1
                    
                except Exception:
                    continue
    except FileNotFoundError:
        print(f"错误: 找不到文件 {filepath}")
        exit(1)

    print(f"\n    读取完成。内存中暂存 {len(raw_triples)} 条三元组。")
    print(f"    检测到 {len(entity_counter)} 个唯一实体，{len(relation_counter)} 个唯一关系。")
    
    # --- 内存中筛选 ---
    print(">>> 正在内存中筛选 Top 实体和关系...")
    
    # 筛选实体：取频次最高的 TARGET_ENTITY_COUNT 个，且频次 >= MIN_ENTITY_FREQ
    most_common_entities = entity_counter.most_common(TARGET_ENTITY_COUNT)
    valid_entities = {e for e, c in most_common_entities if c >= MIN_ENTITY_FREQ}
    
    # 筛选关系：取频次 >= MIN_RELATION_FREQ
    valid_relations = {r for r, c in relation_counter.items() if c >= MIN_RELATION_FREQ}
    
    print(f"    筛选后保留 (Top {TARGET_ENTITY_COUNT}): {len(valid_entities)} 个实体")
    print(f"    筛选后保留 (频次>={MIN_RELATION_FREQ}): {len(valid_relations)} 个关系")
    
    # --- 内存中提取子图 ---
    print(">>> 正在从内存数据中提取最终子图...")
    final_triples = []
    for h, r, t in raw_triples:
        if (h in valid_entities and 
            t in valid_entities and 
            r in valid_relations):
            final_triples.append((h, r, t))
            
    print(f"    子图提取完成。共获取 {len(final_triples)} 个三元组。")
    return final_triples

def map_to_ids(triples):
    print("\n>>> 正在构建 ID 映射...")
    entity2id = {}
    relation2id = {}
    id_triples = []
    
    next_ent_id = 0
    next_rel_id = 0
    
    # 遍历筛选出的三元组重新分配从0开始的ID
    for h, r, t in triples:
        if h not in entity2id:
            entity2id[h] = next_ent_id
            next_ent_id += 1
        if t not in entity2id:
            entity2id[t] = next_ent_id
            next_ent_id += 1
        if r not in relation2id:
            relation2id[r] = next_rel_id
            next_rel_id += 1
            
        id_triples.append((entity2id[h], relation2id[r], entity2id[t]))
    
    print(f"    最终映射：{len(entity2id)} 个实体, {len(relation2id)} 个关系。")
    return id_triples

def split_and_save(triples, output_dir):
    print("\n>>> 正在划分数据集 (8:1:1) 并保存...")
    ensure_dir(output_dir)
    
    random.shuffle(triples)
    
    total = len(triples)
    n_train = int(total * 0.8)
    n_valid = int(total * 0.1)
    
    train_data = triples[:n_train]
    valid_data = triples[n_train : n_train + n_valid]
    test_data = triples[n_train + n_valid:]
    
    def save_file(data, name):
        with open(os.path.join(output_dir, name), 'w') as f:
            for h, r, t in data:
                f.write(f"{h} {r} {t}\n")
        print(f"    已保存 {name}: {len(data)} 条")

    save_file(train_data, 'kg_train.txt')
    save_file(valid_data, 'kg_valid.txt')
    save_file(test_data, 'kg_test.txt')

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"错误: 当前目录下未找到 {SOURCE_FILE}")
        return

    # 1. 单轮扫描：读取、统计、筛选、提取一气呵成
    raw_triples = load_and_filter_one_pass(SOURCE_FILE)
    
    if len(raw_triples) == 0:
        print("警告：未提取到任何三元组，请检查数据源或过滤条件。")
        return

    # 2. ID 映射
    id_triples = map_to_ids(raw_triples)
    
    # 3. 划分保存
    split_and_save(id_triples, OUTPUT_DIR)
    
    print("\n全部任务完成！")

if __name__ == '__main__':
    main()
