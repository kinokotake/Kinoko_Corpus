import csv
import json
import re

csv_file = 'feh_skills.csv'
jsonl_file = 'feh_skills_converted.jsonl'

# 用于匹配各种技能效果里常见的日文全角/半角符号并统一
def clean_text(text):
    if not text:
        return ""
    # 将多余的竖线、空白进行清理
    text = re.sub(r'\s+\|\s+', ' | ', text)
    return text.strip()

with open(csv_file, 'r', encoding='utf-8-sig') as f_in, \
     open(jsonl_file, 'w', encoding='utf-8') as f_out:
    
    reader = csv.reader(f_in)
    headers = next(reader, None)  # 跳过表头
    
    count = 0
    for row in reader:
        if len(row) >= 3:
            skill_name = clean_text(row[0])
            sp_inherit = clean_text(row[1])
            effect = clean_text(row[2])
            
            # 将三列合并为一种“技能图鉴”的阅读格式
            combined_text = f"【{skill_name}】 {sp_inherit} 效果：{effect}"
            
            item = {
                "source": "FEH技能大全",
                "type": "skill_desc",
                "text": combined_text
            }
            f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
            count += 1

print(f"✅ 转换完成！共生成了 {count} 条技能百科数据，保存在 {jsonl_file} 中。")