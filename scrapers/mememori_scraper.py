"""
メメントモリ スキル抓取
source: https://altema.jp/mememori/
Character list: /mememori/charalist  -> /mememori/chara/N
Skill table header: ["スキル", "効果"]
"""
import requests, json, re, time
from bs4 import BeautifulSoup

BASE = "https://altema.jp"
LIST_URL = f"{BASE}/mememori/charalist"
OUTPUT = "../⚔️技能/mememori_skills.jsonl"
SOURCE = "メメントモリスキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.2

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def get_char_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    urls = []
    seen = set()
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "/mememori/chara/" in h and h not in seen:
            seen.add(h)
            full = h if h.startswith("http") else BASE + h
            urls.append(full)
    return urls

def scrape_char(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}"); return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Character name from h1 or title
    h1 = soup.find("h1")
    char_name = clean(h1.get_text()) if h1 else url.split("/")[-1]
    char_name = re.sub(r"【メメントモリ】\s*", "", char_name)  # remove game title prefix
    char_name = re.sub(r"の評価.*", "", char_name).strip()

    skills = []
    # Find tables whose header row is ["スキル","効果"] (or similar 2-col skill tables)
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        if header != ["スキル", "効果"] and "効果" not in header:
            continue
        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            if len(cols) < 2:
                continue
            skill_name = clean(cols[0].get_text())
            effect     = clean(cols[1].get_text())
            if not skill_name or not effect:
                continue
            text = f"【{char_name}：{skill_name}】 効果：{effect}"
            skills.append(text)

    return skills

def main():
    print("Getting character list...")
    char_urls = get_char_urls()
    print(f"Found {len(char_urls)} character pages")

    all_skills = []
    for i, url in enumerate(char_urls, 1):
        print(f"  [{i}/{len(char_urls)}] {url}")
        skills = scrape_char(url)
        all_skills.extend(skills)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_skills)} skill entries")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_skills:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    print("Saved to", OUTPUT)

if __name__ == "__main__":
    main()
