import pandas as pd
import re
import os

# def clean_law_entry(entry):
#     if not isinstance(entry, str):
#         return None
        
#     try:
#         # Split into metadata and content parts
#         # Format: Category-LawNameDate: ArticleID Content
#         if '：' in entry:
#             meta_part, content_part = entry.split('：', 1)
#         else:
#             # Try English colon just in case
#             if ': ' in entry:
#                 meta_part, content_part = entry.split(': ', 1)
#             else:
#                 return None

#         # Extract Law Name
#         # Pattern: Category-LawNameDate
#         # Example: 民法商法-个人独资企业法1999-08-30
#         # We look for the part between the hyphen and the date at the end
#         # Note: Some categories might contain hyphens? Assuming standard format.
#         # We search for the last hyphen before the date? Or just the first hyphen?
#         # Based on example "民法商法-...", likely the first hyphen separates category.
        
#         # Regex to find Law Name:
#         # Find a hyphen, then capture characters until a date pattern at the end of the string.
#         law_name_match = re.search(r'-(.+?)\d{4}-\d{2}-\d{2}$', meta_part)
        
#         if law_name_match:
#             law_name = law_name_match.group(1)
#         else:
#             # Fallback: try to split by hyphen and take the last part if no date, 
#             # or just take the part after the first hyphen.
#             parts = meta_part.split('-')
#             if len(parts) >= 2:
#                 # If date is not present or regex failed, take everything after first hyphen
#                 # But we should try to strip date if it exists but regex failed for some reason
#                 law_name = parts[1]
#                 # Remove date if it's at the end
#                 date_match = re.search(r'\d{4}-\d{2}-\d{2}$', law_name)
#                 if date_match:
#                     law_name = law_name[:date_match.start()]
#             else:
#                 law_name = meta_part

#         # Extract Article ID and Content
#         # Example: 第二十六条 应当解散：,（一）...
#         content_part = content_part.strip()
        
#         # Find the first space which separates Article ID and Content
#         # Article ID usually looks like "第X条"
#         match_article = re.match(r'^(第\S+?条)\s+(.*)', content_part, re.DOTALL)
        
#         if match_article:
#             article_id = match_article.group(1)
#             content_text = match_article.group(2)
#         else:
#             # If no space or pattern doesn't match, treat whole as content or try simple split
#             first_space = content_part.find(' ')
#             if first_space != -1:
#                 article_id = content_part[:first_space]
#                 content_text = content_part[first_space+1:]
#             else:
#                 article_id = "" # Or maybe the whole thing is the article ID? Unlikely.
#                 content_text = content_part

#         # Clean Content
#         # Replace ',（' with '\n（' to fix CSV comma issues
#         content_text = content_text.replace(',（', '\n（')
        
#         # Return formatted string
#         return f"《{law_name}》{article_id}：{content_text}"
        
#     except Exception as e:
#         # print(f"Error processing entry: {entry[:30]}... {e}")
#         return None

def clean_law_entry(entry):
    """
    兼容法律条文和问答类数据的清洗函数
    - 法律条文类：按“第X条”拆分
    - 问答类：直接保留全文
    """
    if not isinstance(entry, str) or not entry.strip():
        return []

    entry = entry.strip()

    # 先尝试提取标题/法律名（如果有“Category-LawNameDate: ”格式）
    if '：' in entry:
        meta_part, content_part = entry.split('：', 1)
    elif ': ' in entry:
        meta_part, content_part = entry.split(': ', 1)
    else:
        meta_part = ''
        content_part = entry  # 整条当正文

    law_name = meta_part.strip() if meta_part else ''

    # 尝试按“第X条”拆分
    pattern = r'(第[\S]+?条)'
    splits = re.split(pattern, content_part)
    
    results = []
    if len(splits) >= 3:
        # splits[0] 可能是标题/前缀，忽略
        for i in range(1, len(splits), 2):
            article_id = splits[i].strip()
            content_text = splits[i+1].strip() if i+1 < len(splits) else ''
            if content_text:
                if law_name:
                    results.append(f"《{law_name}》{article_id}：{content_text}")
                else:
                    results.append(f"{article_id}：{content_text}")
    else:
        # 没有“第X条”，直接保留整条
        results.append(f"《{law_name}》：{content_part}" if law_name else content_part)

    return results


def main():
    # Use absolute path or relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'law_data_3k.csv')
    output_file = os.path.join(script_dir, 'cleaned_law.csv')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Reading {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if 'data' not in df.columns:
        print("Error: Column 'data' not found in CSV.")
        return

    print("Processing data...")
    # Apply the cleaning function
    df['content'] = df['data'].apply(clean_law_entry)
    
    # Drop rows that failed to process (None)
    df_cleaned = df.dropna(subset=['content'])
    
    # Select only the 'content' column
    result_df = df_cleaned[['content']]
    
    print(f"Saving {len(result_df)} entries to {output_file}...")
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print("Success.")

if __name__ == "__main__":
    main()
