"""
シャドウバース カード能力テキスト抓取
source: shadowverse.gamewith.jp
Structure: articles with tables [カード名 | 能力]
"""
import requests, json, re, time
from bs4 import BeautifulSoup
from scrape_utils import safe_write_jsonl

BASE    = "https://shadowverse.gamewith.jp"
# 注意：必须写专属文件，不能用 web_scraped_skills.jsonl —— 那个文件是给手动
# URL 抓取功能用的通用文件，index.html 的 getGame() 只按文件名识别游戏，写进
# web_scraped_skills.jsonl 会导致内容被当成"未知游戏"重新分组，生成第二个重复的
# シャドウバース 筛选按钮（曾经发生过，2026-08-10 修复）。
OUTPUT  = "../⚔️技能/shadowverse_skills.jsonl"
SOURCE  = "シャドウバース"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY   = 1.0

# Card pack articles with カード名|能力 tables
# Each expansion/set has its own article on gamewith
SEED_ARTICLES = [
    "106793",   # アディショナルカード一覧 (large: 200+ tables)
    "441570",   # ヒーローズ・オブ・シャドウバース 新カード
]


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def clean_effect(cell):
    for br in cell.find_all("br"):
        br.replace_with("\n")
    text = cell.get_text(separator="")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    # Drop separator-only lines (----, ====, etc.)
    return "\n".join(line for line in lines if line and not re.fullmatch(r"[-=]{3,}", line))


def get_article_ids_from_top():
    """gamewith トップページからカード一覧記事を収集する。"""
    resp = requests.get(BASE + "/", headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    ids = set(SEED_ARTICLES)
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        m = re.search(r"/article/show/(\d+)", href)
        if m:
            ids.add(m.group(1))
    return list(ids)


def parse_card_effect(card_name, effect_cell):
    """能力セルから進化前/進化後エントリを生成する。"""
    text = clean_effect(effect_cell)
    entries = []

    pre_m = re.search(r"【進化前】([\s\S]+?)(?=【進化後】|$)", text)
    post_m = re.search(r"【進化後】([\s\S]+?)$", text)

    if pre_m and post_m:
        pre = pre_m.group(1).strip()
        post = post_m.group(1).strip()
        if pre:
            entries.append(f"【シャドウバース：{card_name} 進化前】 効果：{pre}")
        if post:
            entries.append(f"【シャドウバース：{card_name} 進化後】 効果：{post}")
    else:
        # Spell / amulet: no evolution split
        body = text.strip()
        # Strip cost/stats prefix (e.g. "3コスト3/1(5/3) 機械")
        body = re.sub(r"^\d+コスト[\d/()]+\s*[\w・]*\s*", "", body).strip()
        if body:
            entries.append(f"【シャドウバース：{card_name}】 効果：{body}")

    return entries


def scrape_article(article_id):
    """記事のすべての「カード名|能力」テーブルを解析する。"""
    url = f"{BASE}/article/show/{article_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    title = clean(soup.title.get_text()) if soup.title else ""

    results = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        # Check header row has カード名 and 能力
        header_cells = rows[0].find_all(["th", "td"])
        header_text = " ".join(c.get_text().strip() for c in header_cells)
        if "カード名" not in header_text or "能力" not in header_text:
            continue

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            card_name = clean(cells[0].get_text())
            if not card_name or len(card_name) < 2:
                continue
            entries = parse_card_effect(card_name, cells[1])
            results.extend(entries)

    return results


def main():
    print("Collecting article IDs...")
    article_ids = get_article_ids_from_top()
    print(f"Found {len(article_ids)} article IDs to check")

    all_entries = []
    seen = set()

    for idx, aid in enumerate(article_ids, 1):
        entries = scrape_article(aid)
        new = [e for e in entries if e not in seen]
        seen.update(new)
        all_entries.extend(new)
        if new:
            print(f"  [{idx}/{len(article_ids)}] article {aid}: +{len(new)} -> total {len(all_entries)}")
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_entries)} entries")

    if safe_write_jsonl(OUTPUT, SOURCE, all_entries):
        print(f"Saved: {len(all_entries)} シャドウバース entries -> {OUTPUT}")


if __name__ == "__main__":
    main()
