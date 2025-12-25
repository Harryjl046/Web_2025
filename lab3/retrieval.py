import os
import torch

# 使用 HuggingFace 国内镜像（防止模型下载失败）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def load_faiss_db():
    """加载本地 FAISS 向量库"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(current_dir, "law_faiss_index")

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at {index_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    embeddings = HuggingFaceEmbeddings(
        model_name="moka-ai/m3e-base",
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": False}
    )

    print(f"Loading FAISS index from {index_path} ...")
    db = FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("FAISS index loaded successfully.")
    return db


# def main():
#     db = load_faiss_db()

#     queries = [
#     "借款人去世后，继承人是否需要履行偿还义务？",
#     "如何通过法律手段应对民间借贷纠纷？",
#     "没有赡养老人就无法继承财产吗？"
# ]

#     for query in queries:
#         print("\n" + "=" * 80)
#         print("Query:", query)
#         results = db.similarity_search(query, k=3)
#         for i, doc in enumerate(results, 1):
#             print(f"[Result {i}]")
#             print(doc.page_content)


def get_retriever(db):
    """封装检索策略，返回配置好的检索器"""
    return db.as_retriever(
        search_type="mmr",  # 开启 MMR
        search_kwargs={
            "k": 3, 
            "fetch_k": 20, 
            "lambda_mult": 0.5
        }
    )

def main():
    db = load_faiss_db()
    retriever = get_retriever(db)

    queries = [
        "借款人去世后，继承人是否需要履行偿还义务？",
        "如何通过法律手段应对民间借贷纠纷？",
        "没有赡养老人就无法继承财产吗？"
    ]

    for query in queries:
        print(f"\n正在进行 MMR 检索，问题: {query}")
        results = retriever.invoke(query)

        for i, doc in enumerate(results, 1):
            print(f"[Result {i}]")
            print(doc.page_content)
            print("-" * 30)


if __name__ == "__main__":
    main()
