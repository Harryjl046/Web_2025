import os
# 如果没有配置系统环境变量，请取消下面这行的注释并填入你的 Key
# os.environ['DASHSCOPE_API_KEY'] = 'your-api-key'

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

    prompt = ChatPromptTemplate.from_template(
        """你是专业的法律知识问答助手。你需要使用以下检索到的上下文片段来回答问题，
禁止根据常识和已知信息回答问题。如果你不知道答案，直接回答“未找到相关答案”。

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


if __name__ == "__main__":
    main()