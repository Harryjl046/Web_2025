import os
import nltk
from pathlib import Path
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from tqdm import tqdm

# 如果是第一次使用，需要先下载一次资源
# nltk.download('punkt')
# nltk.download('stopwords')

#我自定义了下载地址所以需要重新加载地址,如果使用默认下载地址则不需要
nltk.data.path.append("D:/web_experiment/web_2025/nltk_dir")

BASE_DIR = Path(__file__).resolve().parents[1]
input_folder = BASE_DIR / "descriptions"
output_folder = BASE_DIR / "tokenized"
os.makedirs(output_folder, exist_ok=True)

nltk_my_stopwords = BASE_DIR/"nltk_dir/my_stopwords.txt"
with open(nltk_my_stopwords, "r", encoding="utf-8") as f:
    custom_stopwords = {line.strip() for line in f if line.strip()}

tokenizer = RegexpTokenizer(r"[a-zA-Z]+(?:-[a-zA-Z]+)*")

stop_words = set(stopwords.words("english"))
stop_words.update(custom_stopwords)

txt_files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]

for filename in tqdm(txt_files, desc="Tokenizing files", ncols=80):
    
    filepath = os.path.join(input_folder, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read().lower()

    tokens = tokenizer.tokenize(text)

    filtered_tokens = [t for t in tokens if t not in stop_words]

    output_path = os.path.join(output_folder, filename)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(" ".join(filtered_tokens))

print("\nAll documents have been tokenized and saved in:", output_folder)