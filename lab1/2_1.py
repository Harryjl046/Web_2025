import os
from lxml  import etree
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parents[1]
input_folder = BASE_DIR / "test"
output_folder = BASE_DIR / "descriptions"
os.makedirs(output_folder, exist_ok=True)

print(f"📂 输入目录: {input_folder}")
print(f"📂 输出目录: {output_folder}")

xml_files=[f for f in os.listdir(input_folder)if f.endswith(".xml") and f.startswith("PastEvent")] 

for filename in tqdm(xml_files,desc="提取进度",unit="file"):
    file_path = input_folder/filename
    try:
        tree = etree.parse(str(file_path))
        root = tree.getroot()
        
        descriptions = root.findall(".//description")

        description_texts = []
        for desc in descriptions:
            text = ''.join(desc.itertext()).strip()
            if text:
                description_texts.append(text)

        if description_texts:
            output_text = "\n\n".join(description_texts)
            output_name = Path(filename).stem + ".txt"
            output_path = output_folder / output_name

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_text)
        # tqdm 内建议用 postfix 或 logging，不直接 print，以防打断进度条
        # tqdm.write(f"✅ 提取成功: {filename} → {output_name}" if description_texts else f"⚠️ 未找到 Description 标签: {filename}")

    except Exception as e:
        tqdm.write(f"解析失败: {filename} ({e})")