import os
import nltk
from pathlib import Path
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk import pos_tag
from tqdm import tqdm

def get_wordnet_pos(treebank_tag):
    """将词性的Penn Treebank(这什么东西)标记转化为WordNet标记"""
    if treebank_tag.startswith("J"):
        return wordnet.ADJ
    elif treebank_tag.startswith("V"):
        return wordnet.VERB
    elif treebank_tag.startswith("N"):
        return wordnet.NOUN
    elif treebank_tag.startswith("R"):
        return wordnet.ADV
    else:
        return wordnet.NOUN


BASE_DIR = Path(__file__).resolve().parents[2]
input_folder = BASE_DIR / "WEB_2025/lab1/descriptions"
output_folder = BASE_DIR / "WEB_2025/lab1/tokenized"
os.makedirs(output_folder, exist_ok=True)
NLTK_DIR = BASE_DIR / "WEB_2025/lab1/nltk_dir"
NLTK_DIR.mkdir(parents=True, exist_ok=True)     #这是我自定义的nltk数据存放路径
#我自定义了下载地址所以需要重新加载地址,如果使用默认下载地址则不需要
nltk.data.path.append(str(NLTK_DIR)) 

# 如果是第一次使用，需要先下载一次资源，取消掉下面的注释
'''
nltk.download('stopwords', download_dir=str(NLTK_DIR))
nltk.download('punkt', download_dir=str(NLTK_DIR))
nltk.download('averaged_perceptron_tagger_eng', download_dir=str(NLTK_DIR))
nltk.download('wordnet', download_dir=str(NLTK_DIR))
'''

'''
写入自定义停用词文件路径，my_stopwords.txt文件放在了lab1目录下
需要自己修改文件my_stopwords.txt的位置，还有下面的my_stopwords.txt的路径
最后能用就行
'''
nltk_my_stopwords = Path(__file__).resolve().parent / "my_stopwords.txt"


with open(nltk_my_stopwords, "r", encoding="utf-8") as f:
    custom_stopwords = {line.strip() for line in f if line.strip()}
#取词的正则表达式，其意义可以访问regex101.com查看
tokenizer = RegexpTokenizer(r"[a-zA-Z]+(?:-[a-zA-Z]+)*")
#加载停用词
stop_words = set(stopwords.words("english"))
stop_words.update(custom_stopwords)

lemmatizer = WordNetLemmatizer()

txt_files = [f for f in os.listdir(input_folder) if f.endswith(".txt")]

for filename in tqdm(txt_files, desc="Tokenizing files", ncols=80):
    
    filepath = os.path.join(input_folder, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read().lower()
    #分词
    tokens = tokenizer.tokenize(text)
    #去停用词
    filtered_tokens = [t for t in tokens if t not in stop_words]
    #给单词贴词性标签并还原
    pos_tags = pos_tag(filtered_tokens)
    lemmatized_tokens = [
        lemmatizer.lemmatize(word,get_wordnet_pos(pos))
        for word,pos in pos_tags
    ]

    output_path = os.path.join(output_folder, filename)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(" ".join(lemmatized_tokens))

print("\nAll documents have been tokenized and saved in:", output_folder)