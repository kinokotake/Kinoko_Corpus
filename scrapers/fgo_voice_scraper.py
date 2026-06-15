"""
FGO サーヴァントボイス スクレーパー
source: https://kamigame.jp/fgo/サーヴァントボイス/index.html
Structure: index page -> セリフ一覧 links -> 2-col tables (状況 | 台詞)
Output: ../台词/fgo_voice.jsonl
"""
import requests, json, re, time
from bs4 import BeautifulSoup

BASE = "https://kamigame.jp"
INDEX_URL = (BASE + "/fgo/%E3%82%B5%E3%83%BC%E3%83%B4%E3%82%A1%E3%83%B3%E3%83%88"
             "%E3%83%9C%E3%82%A4%E3%82%B9/index.html")
OUTPUT = "../台词/fgo_voice.jsonl"
SOURCE = "FGOサーヴァントボイス"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}
DELAY = 1.3

# Skip keywords for table first-column detection
SKIP_FIRST = {
    'FGO', 'イベント', 'ガチャ', '攻略', 'ランキング', '関連', '編集者',
    'フレンド', '発言者', 'サーヴァント', '注目', '弊社', '声優',
    '関連リンク', '関連記事', '他のサーヴァント',
}
# Skip keywords in situation (col[0]) — navigation / guide items
SKIP_SITUATION = {
    '一覧', '画像', '動画', '掲示板', 'YouTube', '招待',
    'ランキング', '稼ぎ', '種火', 'リセマラ', '礼装', '上げ', '軸',
    '貫通', '解除', '耐性', '効率', '最強', 'ガチャ', 'イベント',
    '幕間', '評価', '攻略', '周回', '報酬', 'クエスト', '素材',
}
# Class names that appear in navigation tables but not as voice situations
CLASS_NAMES = {
    'セイバー', 'アーチャー', 'ランサー', 'ライダー', 'キャスター',
    'アサシン', 'バーサーカー', 'エクストラ', 'ルーラー', 'アヴェンジャー',
}


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def get_voice_urls():
    r = requests.get(INDEX_URL, headers=HEADERS, timeout=20)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    seen = set()
    pages = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        t = a.get_text(strip=True)
        if "セリフ一覧" not in t:
            continue
        if h in seen:
            continue
        seen.add(h)
        name = t.replace("のセリフ一覧", "").strip()
        full = h if h.startswith("http") else BASE + h
        pages.append((name, full))
    return pages


def servant_name_from_h1(soup, fallback):
    h1 = soup.find("h1")
    if not h1:
        return fallback
    raw = clean(h1.get_text())
    raw = re.sub(r"【FGO】\s*", "", raw)
    raw = re.sub(r"のセリフ.*|の(?:台詞|ボイス).*", "", raw).strip()
    return raw if raw else fallback


def scrape_voice(servant_name, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
    except Exception as e:
        print(f"    SKIP {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    servant_name = servant_name_from_h1(soup, servant_name)

    lines = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 1:
            continue
        first_cols = [c.get_text(strip=True) for c in rows[0].find_all(["td", "th"])]
        if len(first_cols) < 2:
            continue
        # Skip non-voice tables by first-column keyword
        if any(skip in first_cols[0] for skip in SKIP_FIRST):
            continue

        for row in rows:
            cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cols) < 2:
                continue
            situation = clean(cols[0])
            voice = clean(cols[1])
            if not situation or not voice:
                continue
            # Skip navigation rows: bare numbers, class names, or guide keywords
            import re as _re
            if _re.match(r"^\d+$", situation):
                continue
            if situation in CLASS_NAMES:
                continue
            if any(skip in situation for skip in SKIP_FIRST | SKIP_SITUATION):
                continue
            # Voice text must look like spoken dialogue
            if "「" not in voice and len(voice) < 15:
                continue
            lines.append(f"【{servant_name}：{situation}】{voice}")

    return lines


def main():
    print("Getting servant voice page list...")
    pages = get_voice_urls()
    print(f"Found {len(pages)} servant voice pages")

    all_lines = []
    for i, (name, url) in enumerate(pages, 1):
        try:
            print(f"  [{i}/{len(pages)}] {name}")
        except Exception:
            print(f"  [{i}/{len(pages)}]")
        lines = scrape_voice(name, url)
        print(f"    -> {len(lines)}")
        all_lines.extend(lines)
        time.sleep(DELAY)

    print(f"\nTotal: {len(all_lines)} voice lines")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for text in all_lines:
            f.write(json.dumps({"source": SOURCE, "type": "", "text": text},
                               ensure_ascii=False) + "\n")
    try:
        print("Saved to", OUTPUT)
    except Exception:
        print("Saved OK")


if __name__ == "__main__":
    main()
