import os
import json

corpus = []
# 遍历当前目录下所有的文件夹
for root, dirs, files in os.walk('.'):
    for file in files:
        # 只读取 txt 和 jsonl 文件
        if file.endswith('.txt') or file.endswith('.jsonl'):
            file_path = os.path.join(root, file)
            # 记录文件所在的文件夹名
            source_name = os.path.relpath(file_path, '.')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        text = line.strip()
                        if text:
                            # 尝试解析 JSONL 格式，把内容提取为纯文本
                            if file.endswith('.jsonl'):
                                try:
                                    obj = json.loads(text)
                                    clean_text = " | ".join([str(v) for v in obj.values() if v])
                                    corpus.append({"source": source_name, "text": clean_text})
                                except:
                                    corpus.append({"source": source_name, "text": text})
                            else:
                                corpus.append({"source": source_name, "text": text})
            except Exception as e:
                print(f"跳过无法读取的文件: {file_path}")

# 保存为网页需要读取的 data.json
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(corpus, f, ensure_ascii=False)

print(f"🎉 打包完成！一共提取了 {len(corpus)} 条语料！")