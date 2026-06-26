"""
プリンセスコネクト Re:Dive スキル抓取
source: https://gamewith.jp/pricone-re/
Skill elements: div.pcr_skill_table
Character list: /pricone-re/article/show/92923
"""
import requests, json, re, time
from bs4 import BeautifulSoup

BASE = "https://gamewith.jp"
LIST_URL = f"{BASE}/pricone-re/article/show/92923"
OUTPUT = "../⚔️技能/pricone_skills.jsonl"
SOURCE = "プリコネスキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept-Language": "ja"}
DELAY = 1.5

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def clean_effect(cell):
    for br in cell.find_all('br'):
        br.replace_with('\n')
    text = cell.get_text(separator='')
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line)

def get_char_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    # Character pages are identified by img[alt=CharName] inside a link
    # (the evaluation list shows character portrait images with alt=name)
    seen = set()
    urls = []
    for img in soup.find_all("img", alt=True):
        alt = img.get("alt", "").strip()
        if not alt or len(alt) > 25:
            continue
        a = img.find_parent("a", href=True)
        if not a:
            continue
        h = a["href"]
        if not re.search(r"/pricone-re/article/show/\d+$", h):
            continue
        if "92923" in h:
            continue
        full = h if h.startswith("http") else BASE + h
        if full not in seen:
            seen.add(full)
            urls.append(full)
    return urls

def scrape_char(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}"); return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Character name from h1
    h1 = soup.find("h1")
    char_name = clean(h1.get_text()) if h1 else ""
    # Extract just the name (before "の評価" etc.)
    char_name = re.sub(r"の評価.*|【.*|｜.*", "", char_name).strip()

    skills = []
    # Skill data lives in div.pcr_skill_table
    for div in soup.find_all("div", class_="pcr_skill_table"):
        text = clean_effect(div)
        if not text:
            continue
        # Skill name is on the first line, before 【説明】/【効果】
        first_line = text.split('\n')[0]
        name_match = re.match(r"^(.+?)(?:【説明】|【効果】)", first_line)
        skill_name = clean(name_match.group(1)) if name_match else clean(first_line[:30])

        prefix = f"【{char_name}：{skill_name}】 " if char_name else f"【{skill_name}】 "
        entry = prefix + text
        skills.append(entry)

    return skills

def main():
    print("Getting character list...")
    char_urls = get_char_urls()
    print(f"Found {len(char_urls)} character pages")

    all_skills = []
    for i, url in enumerate(char_urls, 1):
        print(f"  [{i}/{len(char_urls)}] {url}")
        skills = scrape_char(url)
        print(f"    -> {len(skills)} skills")
        all_skills.extend(skills)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_skills)} skill entries")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_skills:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    print("Saved to", OUTPUT)

if __name__ == "__main__":
    main()
