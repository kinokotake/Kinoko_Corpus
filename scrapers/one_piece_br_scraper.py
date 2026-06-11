"""
ワンピース バウンティラッシュ スキル抓取
source: https://kamigame.jp/onepiece-bountyrush/
Character list: タグ効果ページ (275854715919548138) which links to character pages
Skill structure: div.skill-table-wrap > div.skill-table-header (name+CT)
                 + table.skill-table--description (description in td[1])
"""
import requests, json, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://kamigame.jp"
# This "tag effects" page has actual character links
LIST_URL = f"{BASE}/onepiece-bountyrush/page/275854715919548138.html"
OUTPUT = "../⚔️技能/one_piece_br_skills.jsonl"
SOURCE = "バウンティラッシュスキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.2
MAX_CHARS = 200

SKIP_WORDS = ["一覧", "ランキング", "情報", "ガチャ", "攻略", "メダル",
              "最強", "リセ", "データベース", "クエスト", "編成", "おすすめ",
              "解説", "まとめ", "比較", "評価", "履歴", "確認"]


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def get_char_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    seen = set()
    urls = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        t = a.get_text(strip=True)
        if "/onepiece-bountyrush/page/" not in h:
            continue
        if any(s in t for s in SKIP_WORDS):
            continue
        # Only include short names that look like character names (not guide titles)
        if len(t) > 25 or len(t) < 1:
            continue
        full = h if h.startswith("http") else BASE + h
        if full not in seen:
            seen.add(full)
            urls.append((t, full))
    return urls[:MAX_CHARS]


def scrape_char(char_name, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Get character name from h1 if it's more specific
    h1 = soup.find("h1")
    if h1:
        raw = clean(h1.get_text())
        raw = re.sub(r"【バウンティ】|【OP】|【OPBR】", "", raw)
        name = re.sub(r"の評価.*|のメダル.*|とは.*|｜.*", "", raw).strip()
        if name:
            char_name = name

    skills = []
    # Use div.skill-table-wrap to find skill sections
    for wrap in soup.find_all("div", class_="skill-table-wrap"):
        # Skill name from header
        header = wrap.find("div", class_="skill-table-header")
        if not header:
            continue
        ct_span = header.find("span")
        ct = clean(ct_span.get_text()) if ct_span else ""
        if ct_span:
            ct_span.extract()
        skill_name = clean(header.get_text())

        # Description from skill-table--description
        desc_table = wrap.find("table", class_="skill-table--description")
        if not desc_table:
            continue
        tds = desc_table.find_all("td")
        # First td has skill icon+name again, second td has description
        desc = ""
        for td in tds:
            txt = clean(td.get_text())
            if txt and txt != skill_name and len(txt) > 10:
                desc = txt
                break

        if not skill_name or not desc:
            continue

        ct_part = f" CT：{ct}" if ct else ""
        text = f"【{char_name}：{skill_name}】{ct_part} 効果：{desc}"
        skills.append(text)

    return skills


def main():
    print("Getting character list...")
    char_list = get_char_urls()
    print(f"Found {len(char_list)} character pages (cap {MAX_CHARS})")

    all_skills = []
    for idx, (name, url) in enumerate(char_list, 1):
        try:
            print(f"  [{idx}/{len(char_list)}] {name[:30]}")
        except Exception:
            print(f"  [{idx}/{len(char_list)}]")
        skills = scrape_char(name, url)
        print(f"    -> {len(skills)}")
        all_skills.extend(skills)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_skills)}")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_skills:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    try:
        print("Saved to", OUTPUT)
    except Exception:
        print("Saved OK")


if __name__ == "__main__":
    main()
