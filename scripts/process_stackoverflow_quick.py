"""快速处理Stack Overflow数据 - 只处理1000条"""
import pandas as pd
from bs4 import BeautifulSoup
import json
import re

def clean_html(text):
    """去除HTML标签"""
    if pd.isna(text):
        return ""
    soup = BeautifulSoup(text, 'lxml')
    # 提取代码块
    code_blocks = soup.find_all('code')
    codes = [code.get_text() for code in code_blocks]
    # 提取纯文本
    text = soup.get_text()
    # 清理多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

print("📊 开始处理数据...")

# 读取前1000条
df = pd.read_csv("data/raw/stackoverflow/QueryResults.csv", nrows=1000)
print(f"✅ 读取 {len(df)} 条数据")

# 处理数据
processed_data = []
for idx, row in df.iterrows():
    try:
        cleaned_question = clean_html(row['question'])
        cleaned_answer = clean_html(row['answer'])
        
        # 过滤太短的
        if len(cleaned_question) > 20 and len(cleaned_answer) > 30:
            processed_data.append({
                'id': int(row['id']),
                'question': cleaned_question,
                'answer': cleaned_answer,
                'combined': f"Question: {cleaned_question}\n\nAnswer: {cleaned_answer}"
            })
    except Exception as e:
        print(f"⚠️ 跳过行 {idx}: {e}")
        continue
    
    if (idx + 1) % 100 == 0:
        print(f"  处理进度: {idx + 1}/1000")

print(f"✅ 处理完成！有效数据: {len(processed_data)} 条")

# 保存结果
output_path = "data/processed/stackoverflow_1k.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(processed_data, f, ensure_ascii=False, indent=2)

print(f"💾 保存到: {output_path}")

# 显示样例
print("\n📝 样例数据:")
print(f"Question: {processed_data[0]['question'][:100]}...")
print(f"Answer: {processed_data[0]['answer'][:100]}...")