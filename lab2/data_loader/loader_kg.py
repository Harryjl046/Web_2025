import os
import random
import collections

import torch
import numpy as np
import pandas as pd
from copy import deepcopy


class DataLoaderBase(object):

    def __init__(self, args, logging=None):
        self.args = args
        self.data_name = args.data_name

        self.data_dir = os.path.join(args.data_dir, args.data_name)

        # 直接使用已经划分好的 3 个文件
        self.kg_train_file = os.path.join(self.data_dir, "kg_train.txt")
        self.kg_valid_file = os.path.join(self.data_dir, "kg_valid.txt")
        self.kg_test_file  = os.path.join(self.data_dir, "kg_test.txt")

        # 读取三份 KG（DataFrame）
        self.kg_train_data = self.load_kg(self.kg_train_file)
        self.kg_valid_data = self.load_kg(self.kg_valid_file)
        self.kg_test_data  = self.load_kg(self.kg_test_file)

        if logging:
            logging.info(f"KG train triples: {len(self.kg_train_data)}")
            logging.info(f"KG valid triples: {len(self.kg_valid_data)}")
            logging.info(f"KG test  triples: {len(self.kg_test_data)}")
        else:
            print(f"KG train triples: {len(self.kg_train_data)}")
            print(f"KG valid triples: {len(self.kg_valid_data)}")
            print(f"KG test  triples: {len(self.kg_test_data)}")


    def load_kg(self, filename):
        """
        读取一个 KG 文件为 DataFrame，列名为 ['h', 'r', 't']。
        格式假定：txt文件每行 "h r t"，用空格分隔。
        """
        kg_data = pd.read_csv(
            filename,
            sep=' ',
            names=['h', 'r', 't'],
            engine='python'
        )
        kg_data = kg_data.drop_duplicates()
        return kg_data


    def sample_pos_triples_for_h(self, kg_dict, head, n_sample_pos_triples):
        """
        为head采样正样本。

        """
        pos_triples = kg_dict[head]
        n_pos_triples = len(pos_triples)

        sample_relations, sample_pos_tails = [], []
        while True:
            if len(sample_relations) == n_sample_pos_triples:
                break

            pos_triple_idx = np.random.randint(low=0, high=n_pos_triples, size=1)[0]
            tail = pos_triples[pos_triple_idx][0]
            relation = pos_triples[pos_triple_idx][1]

            if relation not in sample_relations and tail not in sample_pos_tails:
                sample_relations.append(relation)
                sample_pos_tails.append(tail)
        return sample_relations, sample_pos_tails

    def sample_neg_triples_for_h(self, kg_dict, head, relation,
                                 n_sample_neg_triples, highest_neg_idx):
        # TODO
        """
        为给定的 head 采样负样本 tail。

        参数说明：
        kg_dict:           字典，key 为 head 实体，value 为 [(tail, relation), ...] 的列表
        head:              当前要采样负样本的头实体 ID
        relation:          当前使用的关系 ID
        n_sample_neg_triples: 需要采样的负样本数量
        highest_neg_idx:   负样本 tail 的采样上界，一般设为 n_entities，
                           即 tail 从 [0, n_entities) 范围中采样

        采样策略：
        - 随机在 [0, highest_neg_idx) 中采样 tail 候选，要求：
            1.（head,relation,tail）不能是真实存在的正例
            2. 丢弃重复的tail采样
        - 直到采满 n_sample_neg_triples 个负 tail（负样本） 为止。返回
        """
        # 当前 head 在图中的所有正例 (tail, relation) 对
        pos_triples =

        # 用于存放采样到的负 tail
        sample_neg_tails = []
        while True:
            # 当已经采集到足够数量的负样本时，退出循环
            if len(sample_neg_tails) == n_sample_neg_triples:
                break

            # 在 [0, highest_neg_idx) 范围内随机采样一个 tail 作为负样本候选
            tail =

            # 仅当 (tail, relation) 不是正例，且 tail 尚未被采样过时，将其加入 sample_neg_tails
            if

        return sample_neg_tails

    def generate_kg_batch(self, kg_dict, batch_size, highest_neg_idx):
        """
        根据当前 kg_dict（由训练集 + 反向边构成）生成一个 KG batch：

        """
        exist_heads = kg_dict.keys()
        if batch_size <= len(exist_heads):
            batch_head = random.sample(list(exist_heads), batch_size)
        else:
            batch_head = np.random.choice(list(exist_heads),
                                          batch_size,
                                          replace=True).tolist()

        batch_relation, batch_pos_tail, batch_neg_tail = [], [], []
        for h in batch_head:
            relation, pos_tail = self.sample_pos_triples_for_h(kg_dict, h, 1)
            batch_relation += relation
            batch_pos_tail += pos_tail

            neg_tail = self.sample_neg_triples_for_h(
                kg_dict, h, relation[0], 1, highest_neg_idx
            )
            batch_neg_tail += neg_tail

        batch_head = torch.LongTensor(batch_head)
        batch_relation = torch.LongTensor(batch_relation)
        batch_pos_tail = torch.LongTensor(batch_pos_tail)
        batch_neg_tail = torch.LongTensor(batch_neg_tail)
        return batch_head, batch_relation, batch_pos_tail, batch_neg_tail


class DataLoader(DataLoaderBase):
    """
    在 DataLoaderBase 的基础上：
      - 使用 train KG 构建 self.kg_data（带反向边，用于训练 & 采样。即这是真实训练时用的训练集。）
      - 用 train+valid+test 统计 n_entities / n_relations
      - 构建 kg_dict / relation_dict
    """

    def __init__(self, args, logging=None):
        super().__init__(args, logging)

        self.kg_batch_size = args.kg_batch_size
        self.test_batch_size = args.test_batch_size

        self.construct_data()
        self.print_info(logging)

    def construct_data(self):
        """
        在train KG上添加反向三元组，构建训练图self.kg_data；并统计所有数据中的实体数、关系数。

        注：因为由（h,r,t）添加了反向三元组(h,r',t)，且我们此处认为，r和r'是不同的关系，
        所以建模时关系数会因为添加反向三元组而翻倍。
        """

        all_kg_list = [self.kg_train_data, self.kg_valid_data, self.kg_test_data]
        all_kg = pd.concat(all_kg_list, axis=0, ignore_index=True)

        max_ent_id = int(max(all_kg['h'].max(), all_kg['t'].max()))
        self.n_entities = max_ent_id + 1

        max_rel_id = int(all_kg['r'].max())
        n_relations_origin = max_rel_id + 1

        kg_train = self.kg_train_data
        self.n_kg_train = len(kg_train)

        from copy import deepcopy
        reverse_kg_data = deepcopy(kg_train)
        reverse_kg_data['h'], reverse_kg_data['t'] = reverse_kg_data['t'], reverse_kg_data['h']
        reverse_kg_data['r'] = reverse_kg_data['r'] + n_relations_origin

        self.kg_data = pd.concat([kg_train, reverse_kg_data],
                                 axis=0, ignore_index=True)

        max_rel_id_all = int(self.kg_data['r'].max())
        self.n_relations = max_rel_id_all + 1

        self.n_kg_data = len(self.kg_data)
        self.n_kg_valid = len(self.kg_valid_data)
        self.n_kg_test = len(self.kg_test_data)

        import collections
        self.kg_dict = collections.defaultdict(list)
        self.relation_dict = collections.defaultdict(list)

        for _, row in self.kg_data.iterrows():
            h = int(row['h'])
            r = int(row['r'])
            t = int(row['t'])
            self.kg_dict[h].append((t, r))
            self.relation_dict[r].append((h, t))


    def print_info(self, logging=None):
        if logging:
            logging.info('n_entities:   %d' % self.n_entities)
            logging.info('n_relations:  %d' % self.n_relations)
            logging.info('n_kg_train:   %d' % self.n_kg_train)
            logging.info('n_kg_valid:   %d' % self.n_kg_valid)
            logging.info('n_kg_test:    %d' % self.n_kg_test)
            logging.info('n_kg_data(含反向): %d' % self.n_kg_data)
        else:
            print('n_entities:   %d' % self.n_entities)
            print('n_relations:  %d' % self.n_relations)
            print('n_kg_train:   %d' % self.n_kg_train)
            print('n_kg_valid:   %d' % self.n_kg_valid)
            print('n_kg_test:    %d' % self.n_kg_test)
            print('n_kg_data(含反向): %d' % self.n_kg_data)
