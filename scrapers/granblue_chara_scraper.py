"""
グランブルーファンタジー キャラクタースキル抓取
source: https://kamigame.jp/グラブル/キャラクター/
Scrapes each character's 奥義 / アビリティ / サポートアビリティ skill entries.
Output format: 【キャラ名：スキル名】種別：X 効果：Y
"""
import requests, json, re, time
from urllib.parse import unquote
from bs4 import BeautifulSoup
from scrape_utils import safe_write_jsonl

BASE    = "https://kamigame.jp"
INDEX   = f"{BASE}/%E3%82%B0%E3%83%A9%E3%83%96%E3%83%AB/%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC/"
OUTPUT  = "../⚔️技能/granblue_skills.jsonl"
SOURCE  = "グランブルーファンタジースキル"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "ja,en;q=0.5"}
DELAY   = 1.2

# ── 技能区块标题关键词 ─────────────────────────────────────────────
# Ordered by length descending so longer (more specific) patterns match first
# e.g. "サポートアビリティ" must not be shadowed by its substring "アビリティ"
SKILL_SECTIONS = ["サポートアビリティ", "エクストラアビリティ", "アビリティ", "奥義"]
# Higher number = more specific label (wins over generic 奥義)
SECTION_PRIORITY = {"奥義": 1, "アビリティ": 2, "エクストラアビリティ": 3, "サポートアビリティ": 4}

def clean(t):
    return re.sub(r"\s+", " ", (t or "").replace("　", " ")).strip()

def clean_effect(cell):
    for br in cell.find_all("br"):
        br.replace_with("\n")
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in cell.get_text(separator="").split("\n")]
    return "\n".join(l for l in lines if l)

CHARA_PATH = "%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC"  # キャラクター

def get_char_urls():
    """索引页抓取所有角色 URL（hrefs are percent-encoded）"""
    try:
        r = requests.get(INDEX, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
    except Exception as e:
        print(f"Index fetch failed: {e}"); return []

    soup = BeautifulSoup(r.text, "html.parser")
    urls = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if CHARA_PATH + "/" not in href:
            continue
        if not href.endswith(".html"):
            continue
        # Skip generic index pages, keep only character detail pages
        basename = href.split("/")[-1]
        if basename == "index.html":
            continue
        full = href if href.startswith("http") else BASE + href
        if full not in seen:
            seen.add(full)
            urls.append(full)
    return urls

def extract_char_name(url, soup):
    """从 URL 提取角色名，URL 是最可靠的来源"""
    raw = unquote(url.split("/")[-1].replace(".html", ""))
    # 去掉开头的稀有度前缀（SSR / SR / R）
    name = re.sub(r"^(?:SSR|SR|R(?=[^\w]))", "", raw).strip()
    return name or raw

def scrape_char(url):
    """单个角色页 → 技能条目列表"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}"); return []

    soup = BeautifulSoup(r.text, "html.parser")
    char_name = extract_char_name(url, soup)

    # Collect all raw hits first, then resolve best section per skill
    raw_hits = []   # (skill_name, section, cooldown, effect)
    current_section = ""
    in_skill_zone = False

    for tag in soup.find_all(["h2", "h3", "h4", "table"]):
        if tag.name in ("h2", "h3", "h4"):
            txt = clean(tag.get_text())
            matched = None
            for sec in SKILL_SECTIONS:
                if sec in txt:
                    matched = sec
                    break
            if matched:
                current_section = matched
                in_skill_zone = True
            elif in_skill_zone and tag.name == "h2":
                in_skill_zone = False
            continue

        if tag.name != "table" or not in_skill_zone:
            continue

        skill_name = ""
        effect_text = ""
        cooldown = ""
        for row in tag.find_all("tr"):
            tds = row.find_all(["td", "th"])
            if len(tds) < 2:
                continue
            label = clean(tds[0].get_text())
            value_cell = tds[1]
            if label == "名称":
                skill_name = clean(value_cell.get_text())
            elif label in ("効果", "スキル効果"):
                effect_text = clean_effect(value_cell)
            elif label in ("使用間隔", "CT", "リキャスト"):
                cooldown = clean(value_cell.get_text())

        if skill_name and effect_text:
            raw_hits.append((skill_name, current_section, cooldown, effect_text))

    # Build final list: keep first-seen order, but use the most specific section label
    best = {}  # skill_name → (priority, section, cooldown, effect)
    for sname, section, ct, eff in raw_hits:
        p = SECTION_PRIORITY.get(section, 0)
        if sname not in best or p > best[sname][0]:
            best[sname] = (p, section, ct, eff)

    entries = []
    seen = set()
    for sname, section, ct, eff in raw_hits:
        if sname in seen:
            continue
        seen.add(sname)
        _, best_sec, best_ct, best_eff = best[sname]
        parts = [f"種別：{best_sec}"]
        if best_ct:
            parts.append(f"CT：{best_ct}")
        parts.append(f"効果：{best_eff}")
        entries.append(f"【{char_name}：{sname}】 {' '.join(parts)}")

    return entries

def main():
    print("Fetching character index...")
    urls = get_char_urls()
    print(f"Found {len(urls)} character pages")

    all_entries = []
    for i, url in enumerate(urls, 1):
        name = url.split("/")[-1].replace(".html", "")
        entries = scrape_char(url)
        print(f"[{i}/{len(urls)}] {name}: {len(entries)} entries")
        all_entries.extend(entries)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_entries)} entries")
    if safe_write_jsonl(OUTPUT, SOURCE, all_entries):
        print(f"Saved to {OUTPUT}")

if __name__ == "__main__":
    main()
