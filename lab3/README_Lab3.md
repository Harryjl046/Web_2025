# Lab 3: Legal RAG System Data Preprocessing & Vectorization Guide

This guide documents the steps to preprocess legal data, split it into chunks, and create a FAISS vector database for a Retrieval-Augmented Generation (RAG) system.

## 1. Environment Setup

A Conda environment named `rag_env` has been created with the necessary dependencies.

**Activate the environment:**
```powershell
conda activate rag_env
```

**Dependencies installed:**
- python=3.10
- pandas
- langchain
- langchain_community
- langchain-huggingface
- faiss-cpu
- sentence-transformers

## 2. Data Preprocessing

The raw data `law_data_3k.csv` is cleaned and formatted.

**Script:** `preprocess_law.py`

**Functionality:**
- Extracts Law Name and Article ID.
- Cleans content (fixes comma issues).
- Formats output as `《Law Name》ArticleID：Content`.
- Saves to `cleaned_law.csv`.

**Run Command:**
```powershell
python preprocess_law.py
```

## 3. Text Splitting

The cleaned data is loaded and split into manageable chunks for embedding.

**Script:** `split_docs.py`

**Functionality:**
- Loads `cleaned_law.csv` using `CSVLoader`.
- Splits text using `CharacterTextSplitter` (separator=`\n`, chunk_size=500, chunk_overlap=50).
- Returns a list of document chunks.

**Run Command:**
```powershell
python split_docs.py
```

## 4. Vector Database Creation

The document chunks are embedded using a pre-trained model and indexed using FAISS.

**Script:** `create_faiss_db.py`

**Functionality:**
- Imports split documents from `split_docs.py`.
- Initializes `HuggingFaceEmbeddings` with `moka-ai/m3e-base`.
  - *Note: Uses `https://hf-mirror.com` to ensure download stability.*
- Creates a FAISS index from the documents.
- Saves the index locally to the `law_faiss_index` folder.

**Run Command:**
```powershell
python create_faiss_db.py
```

## 5. Output

After running the scripts, you should have:
1.  `cleaned_law.csv`: The preprocessed dataset.
2.  `law_faiss_index/`: A folder containing the FAISS vector index (`index.faiss` and `index.pkl`).

## Troubleshooting

- **Import Errors**: Ensure you are in the `rag_env` environment.
- **Download Timeouts**: The `create_faiss_db.py` script is configured to use a mirror site. If it still fails, check your internet connection or try running it again.
