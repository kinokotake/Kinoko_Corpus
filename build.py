import os
import json

corpus = []

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
                                    # 智能提取：如果存在专门的 'text' 字段就直接取用；若是旧语料有 'utterance' 则取它
                                    main_text = obj.get('text') or obj.get('utterance')
                                    
                                    if main_text:
                                        # 收集所有非正文信息作为“元数据” (除了源文本以外的补充信息)
                                        metadata_parts = []
                                        if 'chapter' in obj:
                                            metadata_parts.append(f"章节: {obj['chapter']}")
                                        if 'speaker' in obj:
                                            metadata_parts.append(f"说话人: {obj['speaker']}")
                                        if 'type' in obj:
                                            metadata_parts.append(f"类型: {obj['type']}")
                                            
                                        meta_str = " | ".join(metadata_parts) if metadata_parts else ""
                                        
                                        corpus.append({
                                            "source": source_name, 
                                            "text": main_text,
                                            "meta": meta_str
                                        })
                                    else:
                                        # 如果没找到特定的正文字段，还是用老办法拼接
                                        clean_text = " | ".join([str(v) for v in obj.values() if v])
                                        corpus.append({"source": source_name, "text": clean_text, "meta": ""})
                                except:
                                    corpus.append({"source": source_name, "text": text, "meta": ""})
                            else:
                                corpus.append({"source": source_name, "text": text, "meta": ""})
            except Exception as e:
                print(f"跳过文件: {file_path}")

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(corpus, f, ensure_ascii=False)

print(f"🎉 优化版打包完成！一共提取了 {len(corpus)} 条干爽的语料！")