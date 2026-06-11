"""
アナザーエデン スキル抓取
source: https://anothereden.game-info.wiki/
Character list: /d/%a1%f95%a5%ad%a5%e3%a5%e9%b0%ec%cd%f7 (☆5キャラ一覧)
Skill table: header ['ランク','スキル名','属性','MP','威力(実質倍率)','特記事項']
Row structure: skill row (6 cols) → '効果' label row → effect text row
"""
import requests, json, re, time
from bs4 import BeautifulSoup

BASE = "https://anothereden.game-info.wiki"
LIST_URL = f"{BASE}/d/%a1%f95%a5%ad%a5%e3%a5%e9%b0%ec%cd%f7"
OUTPUT = "../⚔️技能/another_eden_skills.jsonl"
SOURCE = "アナザーエデンスキル大全"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.5
MAX_CHARS = 250

SKIP_WORDS = ["一覧", "攻略", "Top", "メニュー", "検索", "wiki",
              "パーソナリティ", "グラスタ", "ストーリー", "バトル", "ガチャ", "入手"]
SKILL_HEADER_COLS = {"ランク", "スキル名", "属性", "MP", "威力"}


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def get_char_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(resp.content, "html.parser", from_encoding="euc-jp")
    seen = set()
    urls = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        t = a.get_text(strip=True)
        if "/d/" not in h:
            continue
        if any(s in t for s in SKIP_WORDS):
            continue
        if h not in seen:
            seen.add(h)
            urls.append(h if h.startswith("http") else BASE + h)
    return urls[:MAX_CHARS]


def scrape_char(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return []

    soup = BeautifulSoup(resp.content, "html.parser", from_encoding="euc-jp")
    h1 = soup.find("h1")
    page_title = clean(h1.get_text()) if h1 else url.split("/d/")[-1]
    # The h1 on these pages is the wiki title, not the char name
    # Char name is in the URL or a heading closer to content
    # Try the first h2 or specific heading
    headings = soup.find_all(["h2", "h3"])
    char_name = None
    for hd in headings:
        t = clean(hd.get_text())
        if t and len(t) < 30 and not any(s in t for s in SKIP_WORDS):
            char_name = t
            break
    if not char_name:
        # Fall back to decoding URL component
        from urllib.parse import unquote
        raw = url.split("/d/")[-1]
        try:
            char_name = unquote(raw, encoding="euc-jp")
        except Exception:
            char_name = raw

    skills = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        # Identify skill table by checking for 'スキル名' and 'MP' in header
        if "スキル名" not in header_cells or "MP" not in header_cells:
            continue

        # Parse skill groups: skill-data row → '効果' row → effect-text row
        i = 1
        while i < len(rows):
            cols = rows[i].find_all(["td", "th"])
            cell_texts = [clean(c.get_text()) for c in cols]

            if len(cols) >= 5 and cell_texts[0] not in ("効果", ""):
                # Skill data row
                rank = cell_texts[0]
                skill_name = cell_texts[1] if len(cell_texts) > 1 else ""
                mp = cell_texts[3] if len(cell_texts) > 3 else ""
                power = cell_texts[4] if len(cell_texts) > 4 else ""
                notes = cell_texts[5] if len(cell_texts) > 5 else ""

                # Next row should be '効果' label, then effect text
                effect = ""
                if i + 2 < len(rows):
                    maybe_label = rows[i + 1].find_all(["td", "th"])
                    if maybe_label and clean(maybe_label[0].get_text()) == "効果":
                        effect_row = rows[i + 2].find_all(["td", "th"])
                        if effect_row:
                            effect = clean(effect_row[0].get_text())
                        i += 3
                    else:
                        i += 1
                else:
                    i += 1

                if not skill_name:
                    continue

                parts = [f"【{char_name}：{skill_name}】"]
                if rank:
                    parts.append(f"ランク：{rank}")
                if mp and mp not in ("0", ""):
                    parts.append(f"MP：{mp}")
                if power and power not in ("―", ""):
                    parts.append(f"威力：{power}")
                if notes:
                    parts.append(f"備考：{notes}")
                if effect:
                    parts.append(f"効果：{effect}")
                skills.append(" ".join(parts))
            else:
                i += 1
        break  # only process first matching table

    return skills


def main():
    print("Getting character list...")
    char_urls = get_char_urls()
    print(f"Found {len(char_urls)} character pages (capped at {MAX_CHARS})")

    all_skills = []
    for idx, url in enumerate(char_urls, 1):
        print(f"  [{idx}/{len(char_urls)}] {url}")
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
