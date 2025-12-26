import os
# 如果没有配置系统环境变量，请取消下面这行的注释并填入你的 Key
os.environ['DASHSCOPE_API_KEY'] = 'sk-6a3bd421bfc24f2387f95fb1ae07a7bc'

from retrieval import load_faiss_db, get_retriever

from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    """格式化检索到的文档"""
    return "\n\n".join(doc.page_content for doc in docs)

def build_rag_chain(db):
    print("正在初始化 Qwen 模型和 RAG 链条...")
    """构建 LCEL 问答链"""
    llm = ChatTongyi(model="qwen-plus")

#     prompt = ChatPromptTemplate.from_template(
#         """你是专业的法律知识问答助手。你需要**严格基于下面提供的上下文片段（Context）**回答问题。  
# - 你只能使用 Context 中包含的信息来回答，不允许根据常识、经验或其他法律知识补充内容。  
# - 如果 Context 中包含相关法律条文，优先引用条文回答；如果是问答类内容，在理解的基础上回答。  
# - 剔除上下文中无关信息，避免直接复述无关标题。  
# - 如果 Context 中完全没有相关信息，请只回答“未找到相关答案”。  
# - 不要在回答中提及“根据上下文”或类似措辞，Context 是隐式依据。。
# ”。

    prompt = ChatPromptTemplate.from_template(
        """你是专业的法律知识问答助手。你将严格基于以下检索到的上下文片段回答问题。

指令：
1. 首先，对每条上下文进行简要梳理，提取关键信息（Chain-of-Thought）。  
2. 然后，根据梳理出的信息，给出最终回答（Final Answer）。  
3. 禁止使用常识或模型已有知识，只能依赖提供的上下文。  
4. 如果上下文完全无关，直接回答“未找到相关答案”。  
5. 在回答中不要提及“根据上下文”等表述，回答内容应该自然。
”。

Question: {question}

Context:{context}

Answer:
"""
    )

    retriever = get_retriever(db)

    # LCEL 链条
    rag_chain = (
        RunnableParallel({
            "context": retriever, 
            "question": RunnablePassthrough()
        })
        .assign(
            answer=(
                RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
                | prompt
                | llm
                | StrOutputParser()
            )
        )
    )
    print("RAG 链条构建完成。\n")
    return rag_chain

def main():
    db = load_faiss_db()
    rag_chain = build_rag_chain(db)

    questions = [
        "借款人去世后，继承人是否需要履行偿还义务？",
        "如何通过法律手段应对民间借贷纠纷？",
        "没有赡养老人就无法继承财产吗？"
    ]

    for q in questions:
        print("\n" + "=" * 80)
        print(f"Question: {q}")

        # 调用链
        result = rag_chain.invoke(q)

        print("\nAnswer:")
        # 注意：这里的 key 对应上面 .assign(answer=...) 中的名字
        print(result["answer"])

        print("\nRetrieved Documents:")
        # 注意：这里的 key 对应上面 RunnableParallel 中的 "context"
        for i, doc in enumerate(result["context"], 1):
            print(f"[Doc {i}]")
            print(doc.page_content)
            print("-" * 60)

# def main():
#     db = load_faiss_db()

#     # ⚠️ retriever 要在 main 里单独拿出来
#     retriever = get_retriever(db)

#     rag_chain = build_rag_chain(db)

#     questions = [
#         "借款人去世后，继承人是否需要履行偿还义务？",
#         "如何通过法律手段应对民间借贷纠纷？",
#         "没有赡养老人就无法继承财产吗？"
#     ]

#     for q in questions:
#         print("\n" + "=" * 80)
#         print(f"Question: {q}")

#         # ======== ① 先调试检索 ========
#         docs = retriever.invoke(q)

#         print(f"\n[DEBUG] Retrieved {len(docs)} documents")
#         for i, d in enumerate(docs):
#             print(f"\n--- Doc {i} ---")
#             print(d.page_content[:1000])
#         # ======== 调试结束 ========

#         # ======== ② 再跑 RAG ========
#         result = rag_chain.invoke(q)

#         print("\nAnswer:")
#         print(result["answer"])

#         print("\nRetrieved Documents (from RAG context):")
#         for i, doc in enumerate(result["context"], 1):
#             print(f"[Doc {i}]")
#             print(doc.page_content[:500])
#             print("-" * 60)


if __name__ == "__main__":
    main()
