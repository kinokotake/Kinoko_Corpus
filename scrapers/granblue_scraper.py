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
]

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def scrape_knowledge_page(skill_type, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}"); return []

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = []

    # Extract page overview: h2 headings and their following paragraphs
    for heading in soup.find_all(["h2", "h3"]):
        title = clean(heading.get_text())
        if not title or len(title) < 2:
            continue
        # Collect text from following siblings until next heading
        parts = []
        for sib in heading.find_next_siblings():
            if sib.name in ["h2", "h3"]:
                break
            t = clean(sib.get_text())
            if t and len(t) > 10:
                parts.append(t)
            if sum(len(p) for p in parts) > 500:
                break
        if parts:
            body = " ".join(parts[:3])
            entries.append(f"【{skill_type}：{title}】 解説：{body}")

    # Also extract skill tables (type | grade | description)
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows: continue
        header = [c.get_text(strip=True)[:30] for c in rows[0].find_all(["th","td"])]
        for row in rows[1:]:
            cols = row.find_all(["td","th"])
            if len(cols) < 2: continue
            grade = clean(cols[0].get_text())
            desc  = clean(cols[1].get_text()) if len(cols) > 1 else ""
            if grade and desc and len(desc) > 5:
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
    print("Saved to", OUTPUT)

if __name__ == "__main__":
    main()
