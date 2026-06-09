import os
import json

corpus = []

print("正在扫描本地文件夹...")

for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.txt') or file.endswith('.jsonl'):
            file_path = os.path.join(root, file)
            source_name = os.path.relpath(file_path, '.')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        text = line.strip()
                        if text:
                            if file.endswith('.jsonl'):
                                try:
                                    obj = json.loads(text)
                                    # 兼容性最高的核心文本提取：优先找 text，没有找 utterance，再没有就随便拿一列
                                    main_text = obj.get('text') or obj.get('utterance')
                                    if not main_text and obj.values():
                                        main_text = str(list(obj.values())[0])
                                        
                                    if main_text:
                                        # 收集所有非正文信息作为“元数据” (除了源文本以外的补充信息)
                                        metadata_parts = []
                                        if 'chapter' in obj: metadata_parts.append(f"章节: {obj['chapter']}")
                                        if 'speaker' in obj: metadata_parts.append(f"说话人: {obj['speaker']}")
                                        # 注意这里：如果是技能，我们就不用显示“type”了，因为已经在技能库里了
                                        if 'type' in obj and obj['type'] != 'skill_desc': metadata_parts.append(f"类型: {obj['type']}")
                                            
                                        meta_str = " | ".join(metadata_parts) if metadata_parts else ""
                                        
                                        # 保留 type 以便网页端判断是剧情还是技能
                                        item_type = obj.get('type', '')
                                        
                                        corpus.append({
                                            "source": source_name, 
                                            "text": main_text,
                                            "meta": meta_str,
                                            "type": item_type
                                        })
                                    else:
                                        clean_text = " | ".join([str(v) for v in obj.values() if v])
                                        corpus.append({"source": source_name, "text": clean_text, "meta": "", "type": ""})
                                except:
                                    corpus.append({"source": source_name, "text": text, "meta": "", "type": ""})
                            else:
                                corpus.append({"source": source_name, "text": text, "meta": "", "type": ""})
            except Exception as e:
                print(f"⚠️ 跳过文件 (读取失败): {file_path}")

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(corpus, f, ensure_ascii=False)

print(f"🎉 修复版打包完成！一共提取了 {len(corpus)} 条数据入库！")