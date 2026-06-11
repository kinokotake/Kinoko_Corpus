"""
FGO (Fate/Grand Order) スキル抓取
source: https://kamigame.jp/fgo/
Servant list: /fgo/攻略データベース/サーヴァント一覧/index.html
Skill pattern: table cell col[0] in {スキル, 宝具, スキル1, スキル2, スキル3}
"""
import requests, json, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://kamigame.jp"
LIST_URL = f"{BASE}/fgo/%E6%94%BB%E7%95%A5%E3%83%87%E3%83%BC%E3%82%BF%E3%83%99%E3%83%BC%E3%82%B9/%E3%82%B5%E3%83%BC%E3%83%B4%E3%82%A1%E3%83%B3%E3%83%88%E4%B8%80%E8%A6%A7/index.html"
OUTPUT = "../⚔️技能/fgo_skills.jsonl"
SOURCE = "FGOサーヴァントスキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.5
MAX_SERVANTS = 150

SKILL_LABELS = {"スキル", "宝具", "スキル1", "スキル2", "スキル3", "スキル4", "スキル5"}

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def get_servant_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    urls, seen = [], set()
    for a in soup.find_all("a", href=True):
        h = a["href"]
        # Servant pages: /fgo/page/XXXXXXXX.html or /fgo/攻略データベース/.../index.html
        if ("/fgo/page/" in h or "/fgo/%E6%94%BB%E7%95%A5" in h) and h not in seen and "index.html" not in h:
            seen.add(h)
            full = urljoin(BASE, h)
            urls.append(full)
        elif "/fgo/page/" in h and h not in seen:
            seen.add(h)
            urls.append(urljoin(BASE, h))
    # Also try direct servant sub-paths
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if re.search(r"/fgo/.+/index\.html$", h) and h not in seen:
            seen.add(h)
            urls.append(urljoin(BASE, h))
    return urls[:MAX_SERVANTS]

def scrape_servant(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}"); return []

    soup = BeautifulSoup(resp.text, "html.parser")
    h1 = soup.find("h1") or soup.find("h2")
    raw = clean(h1.get_text() if h1 else "")
    raw = re.sub(r"【FGO】\s*", "", raw)  # remove 【FGO】 prefix
    servant_name = re.sub(r"の(?:性能)?評価.*|の強化.*|とは.*$|｜.*", "", raw).strip()

    skills = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) < 2: continue
            label = clean(cols[0].get_text())
            if label not in SKILL_LABELS: continue
            desc = clean(cols[1].get_text())
            if not desc or len(desc) < 10: continue
            prefix = f"【{servant_name}：{label}】 " if servant_name else f"【{label}】 "
            skills.append(prefix + f"効果：{desc}")

    return skills

def main():
    print("Getting servant list...")
    urls = get_servant_urls()
    print(f"Found {len(urls)} servant pages (cap {MAX_SERVANTS})")
    all_skills = []
    for i, url in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] {url}")
        skills = scrape_servant(url)
        print(f"    -> {len(skills)}")
        all_skills.extend(skills)
        time.sleep(DELAY)
    print(f"\nTotal: {len(all_skills)}")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_skills:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    print("Saved to", OUTPUT)

if __name__ == "__main__":
    main()
