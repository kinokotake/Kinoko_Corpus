import requests
from bs4 import BeautifulSoup
import json
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
}

# Active skills table (628649): cols = name, type, Lv1..Lv5, learnable_units, tags, units
# Passive skills table (751603): cols = name, Lv1..Lv4, learnable_units, units, status, resist
# Link skills table (667487):    cols = name, effect, target, owner_units, units

SKILL_PAGES = [
    ("アクティブスキル", "https://game8.jp/PK_Alterna/628649", "active"),
    ("パッシブスキル",   "https://game8.jp/PK_Alterna/751603", "passive"),
    ("リンクスキル",     "https://game8.jp/PK_Alterna/667487", "link"),
]

OUTPUT_FILE = "⚔️技能/pk_alterna_skills.jsonl"
SOURCE_NAME = "ファンキルオルタナ技能大全"


def clean(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


_LV_NONE_RE = re.compile(r'^※Lv\.\d+なし$')

def get_level_effects(cols, start, count):
    """Return a list of non-empty, non-duplicate level effects, skipping placeholder 'Lv.X なし' rows."""
    effects = []
    for i in range(start, start + count):
        if i >= len(cols):
            break
        t = clean(cols[i].get_text())
        if t and not _LV_NONE_RE.match(t) and t not in effects:
            effects.append(t)
    return effects


def parse_active(rows):
    skills = []
    for row in rows:
        cols = row.find_all(['td', 'th'])
        if len(cols) < 3:
            continue
        name = clean(cols[0].get_text())
        if not name or name == "スキル名":
            continue
        skill_type = clean(cols[1].get_text()) if len(cols) > 1 else ""
        effects = get_level_effects(cols, 2, 5)
        raw_tags = clean(cols[8].get_text()) if len(cols) > 8 else ""
        # Deduplicate and remove empty segments from the tags string
        tag_parts = [t.strip() for t in re.split(r'[、,]', raw_tags) if t.strip()]
        seen = set()
        unique_tags = [t for t in tag_parts if not (t in seen or seen.add(t))]
        tags = "、".join(unique_tags)
        # Build text: name + type + all level effects
        parts = [f"【{name}】"]
        if skill_type:
            parts.append(f"種別：{skill_type}")
        for idx, eff in enumerate(effects, 1):
            label = f"Lv{idx}" if len(effects) > 1 else "効果"
            parts.append(f"{label}：{eff}")
        if tags:
            parts.append(f"タグ：{tags}")
        skills.append(" ".join(parts))
    return skills


def parse_passive(rows):
    skills = []
    for row in rows:
        cols = row.find_all(['td', 'th'])
        if len(cols) < 2:
            continue
        name = clean(cols[0].get_text())
        if not name or name == "スキル名":
            continue
        effects = get_level_effects(cols, 1, 4)
        parts = [f"【{name}】"]
        for idx, eff in enumerate(effects, 1):
            label = f"Lv{idx}" if len(effects) > 1 else "効果"
            parts.append(f"{label}：{eff}")
        skills.append(" ".join(parts))
    return skills


def parse_link(rows):
    skills = []
    for row in rows:
        cols = row.find_all(['td', 'th'])
        if len(cols) < 2:
            continue
        name = clean(cols[0].get_text())
        if not name or name == "スキル":
            continue
        effect = clean(cols[1].get_text()) if len(cols) > 1 else ""
        target = clean(cols[2].get_text()) if len(cols) > 2 else ""
        parts = [f"【{name}】"]
        if effect:
            parts.append(f"効果：{effect}")
        if target:
            parts.append(f"対象：{target}")
        skills.append(" ".join(parts))
    return skills


PARSERS = {
    "active":  parse_active,
    "passive": parse_passive,
    "link":    parse_link,
}


def scrape_page(display_name, url, page_type):
    print(f"Fetching {display_name}: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

    tables = soup.find_all('table')
    # Data table is always table[1] on these pages
    if len(tables) < 2:
        print(f"  WARNING: expected >=2 tables, got {len(tables)}")
        return []

    data_table = tables[1]
    rows = data_table.find_all('tr')
    parser = PARSERS[page_type]
    skills = parser(rows)
    print(f"  -> {len(skills)} entries")
    return skills


def main():
    all_entries = []

    for display_name, url, page_type in SKILL_PAGES:
        entries = scrape_page(display_name, url, page_type)
        all_entries.extend(entries)
        time.sleep(1.5)

    print(f"\nTotal: {len(all_entries)} skill entries")

    if not all_entries:
        print("No data extracted.")
        return

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for text in all_entries:
            obj = {"source": SOURCE_NAME, "type": "skill_desc", "text": text}
            f.write(json.dumps(obj, ensure_ascii=False) + '\n')

    print("Written to", OUTPUT_FILE)


if __name__ == "__main__":
    main()
