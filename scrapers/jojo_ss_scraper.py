"""
ジョジョSS スキル抓取
source: https://gamerch.com/jojo-ss/
Unit list: https://gamerch.com/jojo-ss/548706 (全ユニット一覧)
Skill tables: rows where col[0] in SKILL_LABELS → col[1] = name, row[1] = description
"""
import requests, json, re, time, warnings
warnings.filterwarnings("ignore")
from bs4 import BeautifulSoup

LIST_URL = "https://gamerch.com/jojo-ss/548706"
OUTPUT = "../⚔️技能/jojo_ss_skills.jsonl"
SOURCE = "ジョジョSSスキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.2
MAX_UNITS = 350

SKILL_LABELS = {"リーダースキル", "リンクスキル", "コマンドスキル", "アビリティ", "ブレイクスキル"}


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def get_unit_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20, verify=False)
    soup = BeautifulSoup(resp.text, "html.parser")
    seen = set()
    urls = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if re.match(r"^https://gamerch\.com/jojo-ss/\d+$", h) and h not in seen:
            seen.add(h)
            urls.append((a.get_text(strip=True), h))
    return urls[:MAX_UNITS]


def scrape_unit(unit_name, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Use h1, stripping wiki title wrapper and evaluation suffix
    h1 = soup.find("h1")
    char_name = clean(h1.get_text()) if h1 else unit_name
    char_name = re.sub(r"^【ジョジョSS】", "", char_name).strip()
    char_name = re.sub(r"の評価とステータス.*$", "", char_name).strip()
    if not char_name:
        char_name = unit_name

    skills = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        if not header_cells:
            continue
        label = clean(header_cells[0].get_text())
        if label not in SKILL_LABELS:
            continue

        skill_name = clean(header_cells[1].get_text()) if len(header_cells) > 1 else ""
        desc = ""
        if len(rows) > 1:
            desc_cells = rows[1].find_all(["td", "th"])
            desc = clean(desc_cells[0].get_text()) if desc_cells else ""

        if not skill_name or skill_name == "-" or not desc or desc == "-":
            continue

        text = f"【{char_name}：{skill_name}】 種別：{label} 効果：{desc}"
        skills.append(text)

    return skills


def main():
    print("Getting unit list...")
    unit_list = get_unit_urls()
    print(f"Found {len(unit_list)} unit pages (capped at {MAX_UNITS})")

    all_skills = []
    for idx, (name, url) in enumerate(unit_list, 1):
        print(f"  [{idx}/{len(unit_list)}] {name[:40]}")
        skills = scrape_unit(name, url)
        all_skills.extend(skills)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_skills)} skill entries")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_skills:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    print("Saved to", OUTPUT)


if __name__ == "__main__":
    main()
