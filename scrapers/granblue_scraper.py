"""
グランブルーファンタジー スキル知識ページ抓取
source: https://kamigame.jp/グラブル/
Scrapes encyclopedic skill knowledge pages (攻刃, 連撃, etc.)
Each h3/h4 heading + following paragraph = one entry
"""
import requests, json, re, time
from bs4 import BeautifulSoup

BASE = "https://kamigame.jp"
OUTPUT = "../⚔️技能/granblue_skills.jsonl"
SOURCE = "グランブルーファンタジースキル知識"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.0

SKILL_PAGES = [
    ("攻刃スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E6%94%BB%E5%88%83.html"),
    ("連撃スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E9%80%A3%E6%92%83.html"),
    ("技巧スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E6%8A%80%E5%B7%A7.html"),
    ("背水スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E8%83%8C%E6%B0%B4.html"),
    ("渾身スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E6%B8%BE%E8%BA%AB.html"),
    ("守護スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E5%AE%88%E8%AD%B7.html"),
    ("治癒スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E6%B2%BB%E7%99%92.html"),
    ("ハイブリッドスキル", f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E3%83%8F%E3%82%A4%E3%83%96%E3%83%AA%E3%83%83%E3%83%89.html"),
    ("堅守スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E5%A0%85%E5%AE%88.html"),
    ("軽減スキル",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E8%BB%BD%E6%B8%9B%E7%B3%BB.html"),
    ("防御系スキル",      f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E9%98%B2%E5%BE%A1%E7%B3%BB.html"),
    ("攻撃系スキル",      f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E6%94%BB%E6%92%83%E7%B3%BB.html"),
    ("与ダメージUP",      f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E4%B8%8E%E3%83%80%E3%83%A1%E3%83%BC%E3%82%B8UP.html"),
    ("上限上昇スキル",    f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E3%83%80%E3%83%A1%E3%83%BC%E3%82%B8%E4%B8%8A%E9%99%90%E7%AA%81%E7%A0%B4.html"),
    ("バハ武器スキル",    f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%82%AD%E3%83%AB-%E3%83%90%E3%83%8F%E6%AD%A6%E5%99%A8.html"),
    ("火属性デバフ",     f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95-%E7%81%AB.html"),
    ("水属性デバフ",     f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95-%E6%B0%B4.html"),
    ("土属性デバフ",     f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95-%E5%9C%9F.html"),
    ("風属性デバフ",     f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95-%E9%A2%A8.html"),
    ("光属性デバフ",     f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95-%E5%85%89.html"),
    ("闇属性デバフ",     f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95-%E9%97%87.html"),
    ("デバフ系統",       f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%87%E3%83%90%E3%83%95%E3%81%AE%E7%B3%BB%E7%B5%B1.html"),
    # Additional confirmed knowledge pages from kamigame index
    ("ステータス効果",  f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%82%B9%E3%83%86%E3%83%BC%E3%82%BF%E3%82%B9%E5%8A%B9%E6%9E%9C%E4%B8%80%E8%A6%A7.html"),
    ("バフ相性",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%90%E3%83%95%E7%9B%B8%E6%80%A7.html"),
    ("奥義倍率",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E5%A5%A5%E7%BE%A9%E5%80%8D%E7%8E%87.html"),
    ("弱体成功率",      f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E5%BC%B1%E4%BD%93%E6%88%90%E5%8A%9F%E7%8E%87.html"),
    ("敵対心",          f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E6%95%B5%E5%AF%BE%E5%BF%83.html"),
    ("騎空団サポート",  f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E9%A8%8E%E7%A9%BA%E5%9B%A3%E3%82%B5%E3%83%9D%E3%83%BC%E3%83%88%E3%83%BB%E9%A8%8E%E7%A9%BA%E8%89%A6%E5%8A%B9%E6%9E%9C.html"),
    ("剣心効果",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E5%89%A3%E5%BF%83%E5%8A%B9%E6%9E%9C.html"),
    ("得意武器",        f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E5%BE%97%E6%84%8F%E6%AD%A6%E5%99%A8%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6.html"),
    ("ダメージ減衰",    f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/%E3%83%80%E3%83%A1%E3%83%BC%E3%82%B8%E6%B8%9B%E8%A1%B0.html"),
    ("HP増やし方",      f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%B2%E3%83%BC%E3%83%A0%E7%9F%A5%E8%AD%98/HP%E3%81%AE%E5%A2%97%E3%82%84%E3%81%97%E6%96%B9.html"),
]

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def clean_effect(cell):
    for br in cell.find_all('br'):
        br.replace_with('\n')
    text = cell.get_text(separator='')
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line)

SKIP_TITLES = {"目次", "関連記事", "おすすめ記事", "コメント", "注意事項"}

def is_prose(text):
    """True if text contains a continuous Japanese run of 15+ chars (real prose)."""
    return bool(re.search(r"[぀-鿿]{15,}", text))


def scrape_knowledge_page(skill_type, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}"); return []

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []

    # h2/h3 headings with their following prose paragraphs
    for heading in soup.find_all(["h2", "h3"]):
        title = clean(heading.get_text())
        if not title or len(title) < 2 or title in SKIP_TITLES:
            continue
        parts = []
        for sib in heading.find_next_siblings():
            if sib.name in ["h2", "h3"]:
                break
            if sib.name == "nav":
                continue
            # Skip link-heavy lists (navigation / related-article lists)
            if sib.name in ["ul", "ol"]:
                lis = sib.find_all("li")
                hrefs = sib.find_all("a", href=True)
                if lis and len(hrefs) >= len(lis) * 0.6:
                    continue
            t = clean_effect(sib)
            if t and len(t) > 10 and is_prose(t):
                parts.append(t)
            if sum(len(p) for p in parts) > 600:
                break
        if parts:
            body = "\n".join(parts[:3])
            if is_prose(body):
                entries.append(f"【{skill_type}：{title}】 解説：{body}")

    # Skill tables (grade | description)
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows: continue
        for row in rows[1:]:
            cols = row.find_all(["td","th"])
            if len(cols) < 2: continue
            grade = clean(cols[0].get_text())
            desc  = clean_effect(cols[1]) if len(cols) > 1 else ""
            if grade and desc and len(desc) > 5 and is_prose(desc):
                entries.append(f"【{skill_type}：{grade}】 効果：{desc}")

    return entries

def main():
    all_entries = []
    for skill_type, url in SKILL_PAGES:
        print(f"Fetching {skill_type}")
        entries = scrape_knowledge_page(skill_type, url)
        print(f"  -> {len(entries)} entries")
        all_entries.extend(entries)
        time.sleep(DELAY)
    print(f"\nTotal: {len(all_entries)}")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_entries:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    print("Saved")

if __name__ == "__main__":
    main()
