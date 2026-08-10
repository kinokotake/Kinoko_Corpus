"""
ファイアーエムブレム ヒーローズ スキル一覧抓取
source: https://altema.jp/fe-heroes/skillbetulist/{1,2,3,6,7}
  /1: 武器スキル  /2: 補助スキル  /3: パッシブ  /6: 奥義  /7: 響心
3-col rows: [スキル名, 継承/威力/カウント+効果, SP]
Output: ⚔️技能/feh_skills.jsonl  (JSONL, replaces legacy CSV)
"""
import requests, json, re, time
from bs4 import BeautifulSoup
from scrape_utils import safe_write_jsonl

OUTPUT = "../⚔️技能/feh_skills.jsonl"
SOURCE = "ファイアーエムブレム ヒーローズ"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.5

PAGES = [
    (1, "武器スキル"),
    (2, "補助スキル"),
    (3, "パッシブ"),
    (6, "奥義"),
    (7, "響心"),
]

# Rows to skip per page (navigation/header rows at top of skill table)
SKIP_ROWS = {1: 1, 2: 1, 3: 2, 6: 3, 7: 1}


def clean_effect(cell):
    for br in cell.find_all('br'):
        br.replace_with('\n')
    text = cell.get_text(separator='')
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line)


def get_skill_name(col):
    a = col.find('a', href=True)
    if not a:
        return col.get_text(strip=True)
    name = a.get_text(strip=True)
    if name:
        return name
    img = a.find('img', alt=True)
    if img:
        return img['alt']
    return col.get_text(strip=True)


def scrape_page(page_id, category):
    url = f"https://altema.jp/fe-heroes/skillbetulist/{page_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}"); return []

    soup = BeautifulSoup(r.text, "html.parser")
    rows = [r for r in soup.select("table tr") if len(r.find_all('td')) == 3]
    skip = SKIP_ROWS.get(page_id, 1)
    rows = rows[skip:]

    entries = []
    for row in rows:
        cols = row.find_all('td')
        name = get_skill_name(cols[0]).strip()
        if not name:
            continue
        effect_raw = clean_effect(cols[1])
        sp = cols[2].get_text(strip=True)

        # Build combined text preserving line structure
        # effect_raw example: '【継承】可能 【威力】5\n自分から攻撃した時\n速さ-5'
        combined = f"【{name}】(SP: {sp}) {effect_raw}"
        entries.append(combined)

    return entries


def main():
    all_entries = []
    for page_id, category in PAGES:
        print(f"Fetching page {page_id}: {category}")
        entries = scrape_page(page_id, category)
        print(f"  -> {len(entries)} entries")
        all_entries.extend(entries)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_entries)} entries")
    if safe_write_jsonl(OUTPUT, SOURCE, all_entries):
        print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
