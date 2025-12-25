import os
import sys
import torch
# Set Hugging Face Mirror to avoid connection issues
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Add current directory to sys.path to import split_docs
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from split_docs import load_and_split_docs

def create_vector_db():
    # 1. Get split documents
    print("Fetching split documents...")
    docs = load_and_split_docs()
    
    if not docs:
        print("No documents found.")
        return

    # 2. Initialize Embeddings
    # Using moka-ai/m3e-base as requested for Chinese content

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model_name = "moka-ai/m3e-base"
    model_kwargs = {'device': device}
    encode_kwargs = {'normalize_embeddings': False}
    
    print(f"Initializing HuggingFaceEmbeddings with model: {model_name}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    # 3. Create FAISS Index
    print("Creating FAISS index (this may take a while)...")
    db = FAISS.from_documents(docs, embeddings)

    # 4. Save locally
    output_folder = os.path.join(current_dir, 'law_faiss_index')
    print(f"Saving FAISS index to {output_folder}...")
    db.save_local(output_folder)
    print("Success.")

if __name__ == "__main__":
    create_vector_db()
