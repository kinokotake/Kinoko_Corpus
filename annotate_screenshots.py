# -*- coding: utf-8 -*-
"""
イナイレクロス スクリーンショット標注スクリプト
"""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = r'D:\游戏脚本\游戏截图\イナイレクロス'
OUT  = os.path.join(BASE, 'annotated')
os.makedirs(OUT, exist_ok=True)

RED    = (210, 50,  50)
ORANGE = (220, 130,  0)
GREEN  = (0,  160,  80)
BLUE   = (30, 100, 220)
PURPLE = (150,  50, 200)

def get_font(size):
    for path in [
        r'C:\Windows\Fonts\meiryo.ttc',
        r'C:\Windows\Fonts\YuGothM.ttc',
        r'C:\Windows\Fonts\msgothic.ttc',
    ]:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()

def annotate(filename, boxes):
    """
    boxes: list of ((x1%, y1%, x2%, y2%), color_rgb, label_str)
    坐标使用百分比，方便不同尺寸图片复用
    """
    src = os.path.join(BASE, filename)
    dst = os.path.join(OUT,  filename)
    img = Image.open(src).convert('RGBA')
    W, H = img.size
    print(f"  {filename}: {W}x{H}")

    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    font = get_font(max(26, H // 72))
    label_font = get_font(max(22, H // 90))

    for (x1p, y1p, x2p, y2p), color, label in boxes:
        x1, y1 = int(x1p * W), int(y1p * H)
        x2, y2 = int(x2p * W), int(y2p * H)
        r, g, b = color

        # 半透明fill
        d.rectangle([x1, y1, x2, y2], fill=(r, g, b, 30))
        # 4px border
        for i in range(4):
            d.rectangle([x1+i, y1+i, x2-i, y2-i], outline=(r, g, b, 210))

        # ラベル
        if label:
            tb = d.textbbox((0, 0), label, font=label_font)
            lw, lh = tb[2]-tb[0], tb[3]-tb[1]
            lx = x1
            ly = y1 - lh - 10
            if ly < 5:
                ly = y2 + 6
            d.rectangle([lx-4, ly-4, lx+lw+8, ly+lh+4], fill=(r, g, b, 230))
            d.text((lx+2, ly), label, fill=(255, 255, 255, 255), font=label_font)

    result = Image.alpha_composite(img, overlay).convert('RGB')
    result.save(dst, 'JPEG', quality=92)
    print(f"  → saved: {dst}")

print("=== 标注开始 ===")

# ① クロスシミュレーター.jpg
# 关键标注：24h上限（红）、关闭即停止（红）
annotate('クロスシミュレーター.jpg', [
    ((0.05, 0.405, 0.52, 0.428), RED,  '⚠ 上限24時間'),
    ((0.05, 0.645, 0.52, 0.712), RED,  '⚠ アプリを閉じると停止'),
])

# ② おまかせモード.jpg
# 标注：加速1回=2h（橙）、1日1回无料（橙）、振替加速整体（绿）、7日繰り越し（绿）
annotate('おまかせモード.jpg', [
    ((0.05, 0.295, 0.52, 0.345), ORANGE, '加速1回 = 2時間分'),
    ((0.05, 0.348, 0.52, 0.395), ORANGE, '無料補充：1日1回'),
    ((0.04, 0.44,  0.53, 0.84),  GREEN,  '★ AFK Journey類似設計：振替加速'),
    ((0.05, 0.50,  0.50, 0.57),  GREEN,  '最大7日分まで繰り越し'),
])

# ③ 必殺技.jpg
# 标注：TP消費（蓝）、4種類（蓝）
annotate('必殺技.jpg', [
    ((0.05, 0.185, 0.52, 0.228), BLUE,  'TP消費で発動'),
    ((0.05, 0.235, 0.52, 0.315), BLUE,  '4種類：シュート/ドリブル/ブロック/キーパー'),
])

# ④ パシップ.jpg（パッシブ + 覚醒）
# 标注：覚醒素材（紫）、覚醒段階リスト（紫）
annotate('パシップ.jpg', [
    ((0.05, 0.30, 0.52, 0.38), PURPLE, '覚醒素材：覚醒魂 + 属性のかけら'),
    ((0.05, 0.46, 0.52, 0.82), PURPLE, '覚醒段階（ADVANCE → LEGENDARY）'),
])

# ⑤ 選手.jpg
# 标注：風林火山4属性（蓝）、選手タグ=パッシブ条件（橙）
annotate('選手.jpg', [
    ((0.05, 0.435, 0.52, 0.565), BLUE,   '4属性：風・林・火・山（循環克制）'),
    ((0.05, 0.595, 0.52, 0.735), ORANGE, '選手タグ = パッシブ発動条件'),
])

# ⑥ クロスレベル.jpg
annotate('クロスレベル.jpg', [
    ((0.05, 0.22, 0.52, 0.44), BLUE,   'コアメンバー5人＋レベル均衡制限'),
    ((0.05, 0.47, 0.52, 0.62), ORANGE, 'クロスレベル = 最低レベルが全員の上限'),
])

print("=== 完成 ===")
