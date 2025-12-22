from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import CharacterTextSplitter
import os

def load_and_split_docs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'cleaned_law.csv')
    
    print(f"Loading from {file_path}...")
    # 1. Load data
    # CSVLoader loads each row as a document.
    loader = CSVLoader(file_path=file_path, encoding='utf-8')
    docs = loader.load()
    print(f"Loaded {len(docs)} documents.")
    
    # 2. Split text
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=500,
        chunk_overlap=50
    )
    
    split_docs = text_splitter.split_documents(docs)
    
    return split_docs

if __name__ == "__main__":
    try:
        split_docs = load_and_split_docs()
        print(f"Successfully split into {len(split_docs)} chunks.")
        if len(split_docs) > 0:
            print("-" * 20)
            print("Example chunk content:")
            print(split_docs[0].page_content)
            print("-" * 20)
    except ImportError as e:
        print(f"ImportError: {e}. Please ensure langchain and langchain_community are installed.")
    except Exception as e:
        print(f"An error occurred: {e}")
