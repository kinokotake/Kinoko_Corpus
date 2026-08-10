"""
キングダム乱 スキル抓取
source: https://game8.jp/kingdomran/780604
table[1]: スキル名 | 効果 | 国 | 兵種 | 所属
"""
import requests, json, re, sys
from bs4 import BeautifulSoup
from scrape_utils import safe_write_jsonl

URL = "https://game8.jp/kingdomran/780604"
OUTPUT = "../⚔️技能/kingdom_ran_skills.jsonl"
SOURCE = "キングダム乱スキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}

def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

def clean_effect(cell):
    for br in cell.find_all('br'):
        br.replace_with('\n')
    text = cell.get_text(separator='')
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line)

def main():
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    if len(tables) < 2:
        print("ERROR: expected >=2 tables"); return

    data_table = tables[1]
    rows = data_table.find_all("tr")

    skills = []
    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) < 2:
            continue
        name = clean(cols[0].get_text())
        if not name or name == "スキル名":
            continue
        raw_effect = clean_effect(cols[1])
        country  = clean(cols[2].get_text()) if len(cols) > 2 else ""
        troop    = clean(cols[3].get_text()) if len(cols) > 3 else ""
        faction  = clean(cols[4].get_text()) if len(cols) > 4 else ""

        # Extract 所持キャラ from within effect text, put on same line at end
        char_m = re.search(r'所持キャラ[：:]\s*(\S+)', raw_effect)
        char_name = char_m.group(1).strip() if char_m else ""
        effect = re.sub(r'\s*所持キャラ[：:][\s\S]*$', '', raw_effect).strip()

        parts = [f"【{name}】"]
        if country:    parts.append(f"国：{country}")
        if troop:      parts.append(f"兵種：{troop}")
        if faction:    parts.append(f"所属：{faction}")
        if effect:     parts.append(f"効果：{effect}")
        if char_name:  parts.append(f"所持キャラ：{char_name}")
        skills.append(" ".join(parts))

    print(f"Extracted {len(skills)} skills")
    if safe_write_jsonl(OUTPUT, SOURCE, skills):
        print("Saved to", OUTPUT)

if __name__ == "__main__":
    main()
