"""爬虫共享工具。

背景：another_eden_scraper.py 和 shadowverse_scraper.py 都发生过网站改版/请求失败导致
本次抓取结果为 0 条（或骤降），而脚本原本无条件用 open(OUTPUT, "w") 覆盖旧文件，
好数据被空/残缺数据顶替，还被月度自动化（monthly_scrape.yml）直接提交进了仓库。
safe_write_jsonl 在覆盖前做一次数量检查，抓取结果明显少于现有数据时跳过写入并报警。
"""
import json
import os


def safe_write_jsonl(output_path, source, texts, type_="skill_desc", min_ratio=0.5):
    """将 texts 写为 jsonl（每行 {"source":..., "type":..., "text":...}）。

    若 texts 数量为 0，或明显少于 output_path 现有的行数（低于 min_ratio），
    判定为本次抓取失败，跳过覆盖、保留旧文件不变，并打印 WARNING。

    返回 True 表示已写入新数据，False 表示因疑似失败而跳过。
    """
    new_count = len(texts)

    old_count = 0
    if os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            old_count = sum(1 for line in f if line.strip())

    if old_count > 0 and new_count < old_count * min_ratio:
        print(f"WARNING: skip writing {output_path} - new={new_count} old={old_count} "
              f"(new result is under {min_ratio:.0%} of existing data, looks like a failed scrape)")
        return False

    with open(output_path, "w", encoding="utf-8") as f:
        for text in texts:
            f.write(json.dumps({"source": source, "type": type_, "text": text}, ensure_ascii=False) + "\n")
    return True
