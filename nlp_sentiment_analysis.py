# -*- coding: utf-8 -*-
"""
イナズマイレブン クロス - NLP 情感分析脚本
数据源: Google Play (jp.co.level5.inazumacross)
分析库: asari (日语情感分析)
"""

import sys, io, json, re
from datetime import datetime
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ------------------------------------------------------------------ #
# 1. データ収集
# ------------------------------------------------------------------ #
print("=" * 60)
print("1. Google Playレビュー収集中...")

from google_play_scraper import reviews, Sort

all_reviews = []

# 複数ソートで重複なく取得
for sort_method in [Sort.NEWEST, Sort.MOST_RELEVANT]:
    result, _ = reviews(
        'jp.co.level5.inazumacross',
        lang='ja', country='jp',
        sort=sort_method,
        count=500,
    )
    for r in result:
        all_reviews.append({
            'platform': 'Google Play',
            'reviewId': r.get('reviewId', ''),
            'score': r['score'],
            'content': r['content'],
            'at': r['at'].strftime('%Y-%m-%d') if r.get('at') else '',
            'thumbsUpCount': r.get('thumbsUpCount', 0),
        })

# 重複除去
seen = set()
unique_reviews = []
for r in all_reviews:
    key = r['reviewId'] or r['content'][:50]
    if key not in seen:
        seen.add(key)
        unique_reviews.append(r)

print(f"  取得件数(重複除去後): {len(unique_reviews)}件")

# 空レビューを除外
unique_reviews = [r for r in unique_reviews if r['content'].strip()]
print(f"  有効件数: {len(unique_reviews)}件")

# スコア分布
score_dist = Counter(r['score'] for r in unique_reviews)
print("\n  【スコア分布】")
for s in sorted(score_dist):
    bar = "█" * (score_dist[s] // 3)
    print(f"  ★{s}: {score_dist[s]:3d}件  {bar}")

# ------------------------------------------------------------------ #
# 2. asari による感情分析
# ------------------------------------------------------------------ #
print("\n2. 感情分析中（asari）...")

from asari.api import Sonar
sonar = Sonar()

results_by_score = defaultdict(list)
analyzed = []

for r in unique_reviews:
    text = r['content'].strip()
    if not text:
        continue
    try:
        result = sonar.ping(text)
        label = result['top_class']  # 'positive' or 'negative'
        classes = {c['class_name']: c['confidence'] for c in result['classes']}
        pos_score = classes.get('positive', 0.5)
        neg_score = classes.get('negative', 0.5)
        confidence = abs(pos_score - neg_score)
        r['sentiment_label'] = label
        r['sentiment_pos'] = round(pos_score, 4)
        r['sentiment_neg'] = round(neg_score, 4)
        r['sentiment_confidence'] = round(confidence, 4)
        analyzed.append(r)
        results_by_score[r['score']].append(r)
    except Exception as e:
        r['sentiment_label'] = 'unknown'
        r['sentiment_pos'] = 0.5
        r['sentiment_neg'] = 0.5
        r['sentiment_confidence'] = 0.0
        analyzed.append(r)

print(f"  分析完了: {len(analyzed)}件")

# ------------------------------------------------------------------ #
# 3. 集計
# ------------------------------------------------------------------ #
print("\n3. 結果集計...")

pos_reviews = [r for r in analyzed if r['sentiment_label'] == 'positive']
neg_reviews = [r for r in analyzed if r['sentiment_label'] == 'negative']
neutral_reviews = [r for r in analyzed if r['sentiment_label'] == 'unknown']

print(f"  Positive: {len(pos_reviews)}件 ({len(pos_reviews)/len(analyzed)*100:.1f}%)")
print(f"  Negative: {len(neg_reviews)}件 ({len(neg_reviews)/len(analyzed)*100:.1f}%)")
if neutral_reviews:
    print(f"  Unknown:  {len(neutral_reviews)}件")

# キーワード頻度（形態素なし、簡易N-gram的）
def extract_keywords(reviews_list, top_n=20):
    """よく使われる単語・フレーズを抽出（簡易）"""
    stop_words = {'です', 'ます', 'ない', 'ある', 'いる', 'する', 'なる', 'れる',
                  'られる', 'ください', 'こと', 'もの', 'ので', 'から', 'まで',
                  'とても', 'すごく', 'ちょっと', 'けど', 'でも', 'など', 'また',
                  'ゲーム', 'アプリ', 'プレイ', 'キャラ', 'バトル', 'イナイレ',
                  'イナズマ', 'クロス', 'レベル', '自分', 'もっと', 'やっと',
                  'みんな', 'ほしい', 'ほぼ', 'すべて'}
    words = []
    for r in reviews_list:
        # カタカナ・漢字語を抽出
        tokens = re.findall(r'[ァ-ヶー]{3,}|[一-龥々]{2,}', r['content'])
        words.extend([t for t in tokens if t not in stop_words])
    return Counter(words).most_common(top_n)

pos_keywords = extract_keywords(pos_reviews)
neg_keywords = extract_keywords(neg_reviews)

print("\n  【ポジティブ頻出語】")
for w, c in pos_keywords[:15]:
    print(f"    {w}: {c}回")

print("\n  【ネガティブ頻出語】")
for w, c in neg_keywords[:15]:
    print(f"    {w}: {c}回")

# ------------------------------------------------------------------ #
# 4. 代表コメント抽出
# ------------------------------------------------------------------ #
def get_samples(reviews_list, n=5, label='positive'):
    """信頼度上位のサンプル抽出"""
    sorted_r = sorted(reviews_list, key=lambda x: x['sentiment_confidence'], reverse=True)
    return sorted_r[:n]

top_pos = get_samples(pos_reviews, 8, 'positive')
top_neg = get_samples(neg_reviews, 8, 'negative')

# ★5 ネガティブ / ★1 ポジティブ（矛盾レビュー：興味深い）
star5_neg = [r for r in neg_reviews if r['score'] == 5]
star1_pos = [r for r in pos_reviews if r['score'] == 1]

# ------------------------------------------------------------------ #
# 5. JSONレポート保存
# ------------------------------------------------------------------ #
report_data = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'game': 'イナズマイレブン クロス',
    'app_id': 'jp.co.level5.inazumacross',
    'total_reviews': len(analyzed),
    'score_distribution': {str(k): v for k, v in sorted(score_dist.items())},
    'sentiment_summary': {
        'positive_count': len(pos_reviews),
        'negative_count': len(neg_reviews),
        'positive_ratio': round(len(pos_reviews) / len(analyzed), 4),
        'negative_ratio': round(len(neg_reviews) / len(analyzed), 4),
    },
    'top_positive_keywords': [{'word': w, 'count': c} for w, c in pos_keywords],
    'top_negative_keywords': [{'word': w, 'count': c} for w, c in neg_keywords],
    'sample_positive_reviews': [
        {'score': r['score'], 'content': r['content'][:200], 'confidence': r['sentiment_confidence']}
        for r in top_pos
    ],
    'sample_negative_reviews': [
        {'score': r['score'], 'content': r['content'][:200], 'confidence': r['sentiment_confidence']}
        for r in top_neg
    ],
    'anomaly_star5_negative': [
        {'content': r['content'][:200], 'confidence': r['sentiment_confidence']}
        for r in star5_neg[:3]
    ],
    'all_reviews': analyzed,
}

json_path = r'd:\游戏脚本\Kinoko_Corpus\sentiment_report.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(report_data, f, ensure_ascii=False, indent=2)
print(f"\n4. JSONデータ保存: {json_path}")

# ------------------------------------------------------------------ #
# 6. テキストレポート生成
# ------------------------------------------------------------------ #
def avg_score(reviews_list):
    if not reviews_list: return 0
    return sum(r['score'] for r in reviews_list) / len(reviews_list)

report_lines = []
report_lines.append("=" * 60)
report_lines.append("イナズマイレブン クロス　プレイヤーレビュー感情分析レポート")
report_lines.append(f"生成日時: {report_data['generated_at']}")
report_lines.append("データソース: Google Play (日本語レビュー)")
report_lines.append("=" * 60)
report_lines.append("")

report_lines.append("■ 概要")
report_lines.append(f"  総レビュー数  : {len(analyzed)}件")
report_lines.append(f"  平均スコア    : {avg_score(analyzed):.2f} / 5.0")
report_lines.append(f"  ポジティブ率  : {len(pos_reviews)/len(analyzed)*100:.1f}%  ({len(pos_reviews)}件)")
report_lines.append(f"  ネガティブ率  : {len(neg_reviews)/len(analyzed)*100:.1f}%  ({len(neg_reviews)}件)")
report_lines.append("")

report_lines.append("■ スコア分布")
for s in range(1, 6):
    count = score_dist.get(s, 0)
    pct = count / len(analyzed) * 100
    bar = "█" * (count // 5)
    report_lines.append(f"  ★{s}: {count:3d}件 ({pct:4.1f}%)  {bar}")
report_lines.append("")

report_lines.append("■ ポジティブ頻出テーマ（上位キーワード）")
for w, c in pos_keywords[:12]:
    report_lines.append(f"  {w:　<10} {c}回")
report_lines.append("")

report_lines.append("■ ネガティブ頻出テーマ（上位キーワード）")
for w, c in neg_keywords[:12]:
    report_lines.append(f"  {w:　<10} {c}回")
report_lines.append("")

report_lines.append("■ ポジティブ代表コメント（信頼度上位）")
for i, r in enumerate(top_pos, 1):
    report_lines.append(f"  [{i}] ★{r['score']}  (確信度:{r['sentiment_confidence']:.3f})")
    report_lines.append(f"      {r['content'][:150]}")
    report_lines.append("")

report_lines.append("■ ネガティブ代表コメント（信頼度上位）")
for i, r in enumerate(top_neg, 1):
    report_lines.append(f"  [{i}] ★{r['score']}  (確信度:{r['sentiment_confidence']:.3f})")
    report_lines.append(f"      {r['content'][:150]}")
    report_lines.append("")

if star5_neg:
    report_lines.append("■ 注目：★5なのにネガティブ感情（内容に不満を含む）")
    for r in star5_neg[:3]:
        report_lines.append(f"  {r['content'][:200]}")
        report_lines.append("")

report_text = "\n".join(report_lines)
txt_path = r'd:\游戏脚本\Kinoko_Corpus\sentiment_report.txt'
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write(report_text)

print(f"5. テキストレポート保存: {txt_path}")
print("\n" + report_text)
