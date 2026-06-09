import os
import json
import csv
import re

corpus = []
print("正在扫描本地文件夹...")

def clean_csv_text(text):
    if not text: return ""
    return re.sub(r'\s+\|\s+', ' | ', text).strip()

for root, dirs, files in os.walk('.'):
    for file in files:
        file_path = os.path.join(root, file)
        source_name = os.path.relpath(file_path, '.')

        if file.endswith('.csv') and 'feh_skills' in file.lower():
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    for row in reader:
                        if len(row) >= 3:
                            skill_name = clean_csv_text(row[0])
                            effect_text = clean_csv_text(row[1]).replace(' | ', ' ')
                            sp_text = clean_csv_text(row[2])
                            combined_text = f"【{skill_name}】(SP: {sp_text}) {effect_text}"
                            corpus.append({
                                "source": source_name, 
                                "text": combined_text,
                                "meta": "",  
                                "type": "skill_desc"  
                            })
            except Exception as e:
                print(f"⚠️ 跳过 CSV 文件: {file_path}")

        elif file.endswith('.txt') or file.endswith('.jsonl'):
            if file.lower() == 'feh_skills_converted.jsonl':
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        text = line.strip()
                        if text:
                            if file.endswith('.jsonl'):
                                try:
                                    obj = json.loads(text)
                                    main_text = obj.get('text') or obj.get('utterance')
                                    if not main_text and obj.values():
                                        main_text = str(list(obj.values())[0])
                                    if main_text:
                                        metadata_parts = []
                                        if 'chapter' in obj: metadata_parts.append(f"章节: {obj['chapter']}")
                                        if 'speaker' in obj: metadata_parts.append(f"说话人: {obj['speaker']}")
                                        if 'type' in obj and obj['type'] != 'skill_desc': metadata_parts.append(f"类型: {obj['type']}")
                                        meta_str = " | ".join(metadata_parts) if metadata_parts else ""
                                        item_type = obj.get('type', '')
                                        corpus.append({"source": source_name, "text": main_text, "meta": meta_str, "type": item_type})
                                    else:
                                        clean_text = " | ".join([str(v) for v in obj.values() if v])
                                        corpus.append({"source": source_name, "text": clean_text, "meta": "", "type": ""})
                                except:
                                    corpus.append({"source": source_name, "text": text, "meta": "", "type": ""})
                            else:
                                corpus.append({"source": source_name, "text": text, "meta": "", "type": ""})
            except Exception as e:
                print(f"⚠️ 跳过文本文件: {file_path}")

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(corpus, f, ensure_ascii=False)

print(f"🎉 究极完美版打包完成！一共提取了 {len(corpus)} 条数据入库！")