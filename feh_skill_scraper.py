import requests
from bs4 import BeautifulSoup
import csv
import re

# 抓取A级被动技能
TARGET_URL = "https://altema.jp/fe-heroes/skillbetulist/1"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
}

def clean_html(element):
    """提取标签内的纯文本，处理 <br> 并清理多余空格"""
    if not element:
        return ""
    # 将 <br> 替换成竖线，方便阅读和后续切分
    for br in element.find_all('br'):
        br.replace_with(' | ')
    return " ".join(element.get_text(strip=True).split())

def main():
    print(f"🚀 正在连接 Altema 网站获取技能数据: {TARGET_URL}")
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"❌ 网络请求失败: {e}")
        return

    # 分析 Altema 的技能列表：
    # 它们通常包裹在 div class="wikitb" 或类似的表格结构中
    # 每一行技能数据对应一个 tr 标签
    rows = soup.select('table tr')
    
    if not rows:
        print("❌ 未能在页面中找到任何表格结构！")
        return

    all_data = []
    # 设定表头
    headers = ["スキル名 (技能名)", "習得SP/継承 (SP/继承)", "効果 (效果)"]
    all_data.append(headers)
    
    skill_count = 0

    for row in rows:
        # A技能列表的典型结构：
        # td 1: 技能图片 + 技能名字 + 射程等
        # td 2: SP / 继承限制
        # td 3: 技能效果
        cols = row.find_all('td')
        
        # 我们只抓取正好有 3 列的数据行 (这就是技能行的特征)
        if len(cols) == 3:
            # 1. 提取技能名（尝试找到加粗的 <b> 或 <a> 标签）
            skill_name_elem = cols[0].find('a') or cols[0].find('b') or cols[0]
            skill_name = clean_html(skill_name_elem)
            
            # 如果名字提取出来为空，说明不是有效的技能行
            if not skill_name or skill_name == "スキル名": 
                continue
                
            # 2. 提取 SP/继承 信息
            sp_inherit = clean_html(cols[1])
            
            # 3. 提取效果描述
            effect = clean_html(cols[2])
            
            all_data.append([skill_name, sp_inherit, effect])
            skill_count += 1

    if skill_count > 0:
        output_file = 'feh_skills.csv'
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(all_data)
        print(f"✅ 抓取成功！共精准提取了 {skill_count} 个技能。")
        print(f"📂 技能表已保存为: {output_file}，请用 Excel 打开查看！")
    else:
        print("⚠️ 网页中没有找到符合【技能名-SP-效果】三列特征的数据行。")

if __name__ == "__main__":
    main()