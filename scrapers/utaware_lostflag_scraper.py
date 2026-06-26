"""
うたわれるもの ロストフラグ スキル抓取
source: https://appmedia.jp/utaware-lostflag/
Character list: /utaware-lostflag/4664383 (全キャラ一覧)
Skill tables per page:
  CharNameの通常攻撃 → 範囲/速度/回数/効果 columns, description in last col
  CharNameの連撃    → 段階/範囲/効果 structure, description in <td colspan=4 text-align:left>
  CharNameの特性    → rows after title = trait descriptions
"""
import requests, json, re, time
from bs4 import BeautifulSoup

BASE      = "https://appmedia.jp"
LIST_URL  = f"{BASE}/utaware-lostflag/4664383"
OUTPUT    = "../⚔️技能/utaware_lostflag_skills.jsonl"
SOURCE    = "うたわれるもの ロストフラグ"
HEADERS   = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY     = 1.2
MAX_CHARS = 700


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def clean_effect(cell):
    for br in cell.find_all("br"):
        br.replace_with("\n")
    text = cell.get_text(separator="")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


SKIP_WORDS = {"一覧", "ランキング", "攻略", "最強", "おすすめ", "まとめ",
              "評価", "縁結び", "ガチャ", "情報", "方法", "確認", "解説"}

def get_char_urls():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    seen, urls = set(), []
    # Character links live inside table cells with short Japanese name text
    for a in soup.select("table a[href]"):
        href = a["href"]
        text = a.get_text(strip=True)
        if not re.search(r"/utaware-lostflag/\d{7,}$", href):
            continue
        if not text or len(text) > 14:
            continue
        if any(w in text for w in SKIP_WORDS):
            continue
        full = href if href.startswith("http") else BASE + href
        if full not in seen:
            seen.add(full)
            urls.append(full)
    return urls[:MAX_CHARS]


def extract_renngeki(table, char_name):
    """連撃テーブルから各段階の説明文を抽出して一エントリにまとめる。"""
    descs = []
    for td in table.find_all("td"):
        style = td.get("style", "")
        colspan = td.get("colspan", "1")
        # Description cells: colspan=4, text-align:left
        if colspan == "4" and "text-align" in style:
            text = clean_effect(td)
            if text and len(text) > 5:
                descs.append(text)
    if not descs:
        return None
    combined = "\n".join(descs)
    return f"【うたわれるもの ロストフラグ：{char_name} 連撃】 効果：{combined}"


def extract_tsujou(table, char_name):
    """通常攻撃テーブルから効果説明を抽出する。"""
    rows = table.find_all("tr")
    for row in rows[2:]:   # skip title row and header row
        cols = row.find_all(["td", "th"])
        if not cols:
            continue
        # Last column = 効果
        desc = clean_effect(cols[-1])
        if desc and len(desc) > 3:
            return f"【うたわれるもの ロストフラグ：{char_name} 通常攻撃】 効果：{desc}"
    return None


def extract_tokusei(table, char_name):
    """特性テーブルから各特性説明を抽出して一エントリにまとめる。"""
    rows = table.find_all("tr")
    parts = []
    for row in rows[1:]:   # skip title row
        cols = row.find_all(["td", "th"])
        for col in cols:
            text = clean_effect(col)
            if text and len(text) > 5:
                parts.append(text)
    if not parts:
        return None
    combined = "\n".join(parts)
    return f"【うたわれるもの ロストフラグ：{char_name} 特性】 効果：{combined}"


def scrape_char(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Character name from h1 (strip game title prefix and evaluation suffix)
    h1 = soup.find("h1")
    raw = clean(h1.get_text()) if h1 else ""
    raw = re.sub(r"^【うたわれるもの\s*ロストフラグ】\s*", "", raw)
    char_name = re.sub(r"の評価.*|とは.*|｜.*", "", raw).strip()
    if not char_name:
        return []

    skills = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        title_cell = rows[0].find(["th", "td"])
        if not title_cell:
            continue
        title = clean(title_cell.get_text())

        if title == f"{char_name}の連撃":
            entry = extract_renngeki(table, char_name)
            if entry:
                skills.append(entry)

        elif title == f"{char_name}の通常攻撃":
            entry = extract_tsujou(table, char_name)
            if entry:
                skills.append(entry)

        elif title == f"{char_name}の特性":
            entry = extract_tokusei(table, char_name)
            if entry:
                skills.append(entry)

    return skills


def main():
    print("Getting character list...")
    char_urls = get_char_urls()
    print(f"Found {len(char_urls)} candidate pages (cap {MAX_CHARS})")

    all_skills = []
    found_chars = 0
    for idx, url in enumerate(char_urls, 1):
        skills = scrape_char(url)
        if skills:
            found_chars += 1
            all_skills.extend(skills)
            if idx % 20 == 0 or skills:
                print(f"  [{idx}/{len(char_urls)}] +{len(skills)} -> total {len(all_skills)}")
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_skills)} entries from {found_chars} characters")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_skills:
            f.write(json.dumps({"source": SOURCE, "type": "skill_desc", "text": text}, ensure_ascii=False) + "\n")
    print("Saved OK")


if __name__ == "__main__":
    main()
