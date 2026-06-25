"""
ファンキルオルタナ JSONL 后处理
原始数据将 【1】：/【2】：块、※注释、【範囲/...】标签压在一行
本脚本还原换行，使格式与原网页一致
"""
import json, re, pathlib

INPUT  = pathlib.Path("../⚔️技能/pk_alterna_skills.jsonl")
OUTPUT = INPUT  # 原地覆写

def fix_effect(text):
    # 1. 【N】：块：在【N】：前插入换行，但仅当前面不是全角冒号（即不是 LvN：开头）
    text = re.sub(r'(?<!：)【(\d)】：', r'\n【\1】：', text)
    # 2. ※注释：每个※前换行
    text = re.sub(r'(?<!\n)※', r'\n※', text)
    # 3. 【範囲/...】/【消費SP】标签块：前面的空格换成换行
    text = re.sub(r' (【(?:範囲|単体|自身|全体)[^】]*】/【消費SP】)', r'\n\1', text)
    # 4. 去掉末尾多余的 タグ：xxx（已在标签块里体现）
    text = re.sub(r'\s*タグ：\S+$', '', text)
    return text

lines = INPUT.read_text(encoding='utf-8').splitlines()
out = []
for line in lines:
    if not line.strip():
        continue
    obj = json.loads(line)
    obj['text'] = fix_effect(obj['text'])
    out.append(json.dumps(obj, ensure_ascii=False))

OUTPUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
print(f"Done: {len(out)} entries -> {OUTPUT}")
