import torch
import torch.nn as nn
import torch.nn.functional as F


def _L2_loss_mean(x):
    return torch.mean(torch.sum(torch.pow(x, 2), dim=1, keepdim=False) / 2.)


class Embedding_based(nn.Module):
    """
    纯 KGE 模型：
      - 支持 TransE / TransR
    """

    def __init__(self, args, n_entities, n_relations):
        # TODO 必做

        super(Embedding_based, self).__init__()

        self.use_pretrain = args.use_pretrain
        self.KG_embedding_type = args.KG_embedding_type  # 'TransE' 或 'TransR'

        self.kg_l2loss_lambda = args.kg_l2loss_lambda
        
        self.n_entities = 
        self.n_relations = 

        self.embed_dim =           # 实体向量维度
        self.relation_dim =        # 关系向量维度

        # ---- KG embeddings ----
        self.entity_embed = 
        self.relation_embed = 
        nn.init.xavier_uniform_(self.entity_embed.weight)
        nn.init.xavier_uniform_(self.relation_embed.weight)

        # ---- TransR: 每个关系一个投影矩阵 W_r in R^{embed_dim x relation_dim} ----
        # 若只做 TransE，可以不用这个，但为了兼容性保留
        self.trans_M = nn.Parameter(
            torch.Tensor(self.n_relations, self.embed_dim, self.relation_dim)
        )
        nn.init.xavier_uniform_(self.trans_M)

    # ===================================================================
    # TransR loss
    # ===================================================================
    def calc_kg_loss_TransR(self, h, r, pos_t, neg_t):
        # TODO（选做）
        """
        使用 TransR 模型计算一批训练样本的 KG 损失（pairwise BPR 风格）

        输入：
        h:      LongTensor，形状 (B,) —— 头实体索引
        r:      LongTensor，形状 (B,) —— 关系索引
        pos_t:  LongTensor，形状 (B,) —— 正尾实体索引
        neg_t:  LongTensor，形状 (B,) —— 负尾实体索引
        """
        r_embed =                         # (B, relation_dim)
        W_r =                             # (B, embed_dim, relation_dim)
  
        h_embed =                         # (B, embed_dim)
        pos_t_embed =                     # (B, embed_dim)
        neg_t_embed =                     # (B, embed_dim)

        # 1. 投影到关系空间
        r_mul_h =                         # (B, relation_dim)
        r_mul_pos_t =                     # (B, relation_dim)
        r_mul_neg_t =                     # (B, relation_dim)
 
        # 2. L2 归一化
        r_embed = 
        r_mul_h = 
        r_mul_pos_t = 
        r_mul_neg_t = 

        # 3. 得分
        pos_score =                       # (B,)
        neg_score =                       # (B,)

        # 4. BPR 风格的 pairwise loss
        kg_loss =                         # 基于pos_score，neg_score，补全BPR loss
        kg_loss = torch.mean(kg_loss)

        l2_loss = (
            _L2_loss_mean(r_mul_h)
            + _L2_loss_mean(r_embed)
            + _L2_loss_mean(r_mul_pos_t)
            + _L2_loss_mean(r_mul_neg_t)
        )
        loss = kg_loss + self.kg_l2loss_lambda * l2_loss
        return loss

    def score_TransR(self, h, r, t):
        # TODO（选做）
        """
        使用 TransR 模型对一批三元组 (h, r, t) 计算打分（距离）。

        输入：
        h, r, t: LongTensor, 形状均为 (B,)
                 分别表示头实体索引、关系索引、尾实体索引

        输出：
        score: FloatTensor, 形状 (B,)
               为每个三元组在关系空间中的距离 || h_r + r - t_r ||_2，
        """

        # 1. 取出关系嵌入 r_embed 以及对应的投影矩阵 W_r
        r_embed =                         # (B, relation_dim)
        W_r =                             # (B, embed_dim, relation_dim)

        # 2. 取出头实体和尾实体的嵌入向量 h_embed, t_embed
        h_embed =                         # (B, embed_dim)
        t_embed =                         # (B, embed_dim)

        # 3. 将实体嵌入映射到关系空间：
        r_mul_h =                         # (B, relation_dim)
        r_mul_t =                         # (B, relation_dim)

        # 4. 对 r_embed, r_mul_h, r_mul_t 进行 L2 归一化（按行）
        r_embed = 
        r_mul_h = 
        r_mul_t = 

        # 5. 根据 TransR 的打分函数计算距离：
        score =                           # (B,)

        return score

    # ===================================================================
    # TransE loss
    # ===================================================================
    def calc_kg_loss_TransE(self, h, r, pos_t, neg_t):
        # TODO 必做
        """
        使用 TransE 模型计算一批训练样本的 KG 损失（pairwise BPR 风格）

        h:      (kg_batch_size)
        r:      (kg_batch_size)
        pos_t:  (kg_batch_size)
        neg_t:  (kg_batch_size)
        注意：为保证 (h + r - t) 可加减，一般需设 relation_dim == embed_dim。
        """
        r_embed =                          # (B, relation_dim)

        h_embed =                          # (B, embed_dim)
        pos_t_embed =                      # (B, embed_dim)
        neg_t_embed =                      # (B, embed_dim)

        # 归一化
        r_embed = 
        h_embed =
        pos_t_embed =
        neg_t_embed =

        # 得分
        pos_score =                        # (B,)
        neg_score =                        # (B,)

        # BPR 风格 pairwise loss
        kg_loss =
        kg_loss = torch.mean(kg_loss)

        l2_loss = (
            _L2_loss_mean(h_embed)
            + _L2_loss_mean(r_embed)
            + _L2_loss_mean(pos_t_embed)
            + _L2_loss_mean(neg_t_embed)
        )
        loss = kg_loss + self.kg_l2loss_lambda * l2_loss
        return loss

    def score_TransE(self, h, r, t):
        # TODO 必做
        """
        计算 TransE 的打分函数 score(h, r, t)。

        输入：
        h: LongTensor，头实体的索引 (batch_size,)
        r: LongTensor，关系的索引     (batch_size,)
        t: LongTensor，尾实体的索引 (batch_size,)

        """

        # 根据索引取对应的嵌入向量
        r_embed = 
        h_embed =
        t_embed =

        # 对嵌入进行归一化（按行进行 L2 归一化）
        r_embed = 
        h_embed =
        t_embed =        

        # 根据 TransE 的距离函数计算得分：|| h + r - t ||_2
        score = 

        return score


    # ===================================================================
    # 统一接口
    # ===================================================================
    def calc_loss(self, h, r, pos_t, neg_t):

        if self.KG_embedding_type == 'TransR':
            return self.calc_kg_loss_TransR(h, r, pos_t, neg_t)
        elif self.KG_embedding_type == 'TransE':
            return self.calc_kg_loss_TransE(h, r, pos_t, neg_t)
        else:
            raise ValueError(f"Unknown KG_embedding_type: {self.KG_embedding_type}")

    def calc_score(self, h, r, t):

        if self.KG_embedding_type == 'TransR':
            return self.score_TransR(h, r, t)
        elif self.KG_embedding_type == 'TransE':
            return self.score_TransE(h, r, t)
        else:
            raise ValueError(f"Unknown KG_embedding_type: {self.KG_embedding_type}")

    def forward(self, h, r, pos_t, neg_t, is_train=True):

        if is_train:
            return self.calc_loss(h, r, pos_t, neg_t)
        else:
            return self.calc_score(h, r, pos_t)
