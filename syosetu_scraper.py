import requests
from bs4 import BeautifulSoup
import json
import time
import re

# 目标小说的目录页（ncode）
BASE_URL = "https://ncode.syosetu.com/n3126mf/"

# 强化版请求头，更像真实的浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6',
    'Referer': 'https://yomou.syosetu.com/'
}

def get_chapter_links():
    """获取小说目录页中所有章节的链接"""
    print(f"正在获取小说目录: {BASE_URL}")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status() # 如果请求失败（比如404或403），会直接报错
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        # Syosetu 的章节列表通常在 class="p-eplist__sublist" 或 <dd class="subtitle"> 下
        # 我们用更宽泛的查找方式：寻找 href 中包含 /n3126mf/ 的链接
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # 匹配章节链接，例如 /n3126mf/1/
            if re.match(r'^/n3126mf/\d+/?$', href):
                full_link = f"https://ncode.syosetu.com{href}"
                title = a_tag.text.strip()
                if full_link not in [l[1] for l in links]: # 防止重复
                    links.append((title, full_link))
                
        print(f"成功获取到 {len(links)} 个章节！")
        return links
    except Exception as e:
        print(f"获取目录失败: {e}")
        return []

def scrape_chapter(title, url):
    """抓取单个章节的内容，并区分对话和旁白"""
    print(f"正在抓取章节: {title} ...", end=" ")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试多种可能的正文容器 ID/Class
        honbun = soup.find('div', id='novel_honbun') or soup.find('div', class_='p-novel__body')
        
        if not honbun:
            print("未找到正文！")
            return []

        lines_data = []
        for p in honbun.find_all('p'):
            text = p.text.strip()
            if not text:
                continue
                
            if text.startswith('「') or text.startswith('『'):
                clean_text = re.sub(r'^[「『](.*?)[」』]$', r'\1', text)
                line_type = "dialogue"
            else:
                clean_text = text
                line_type = "narration"

            lines_data.append({
                "source_url": url,
                "chapter": title,
                "type": line_type,
                "text": clean_text
            })
            
        print(f"完成! 提取到 {len(lines_data)} 行。")
        return lines_data
    except Exception as e:
        print(f"抓取章节失败: {e}")
        return []

def main():
    chapters = get_chapter_links()
    if not chapters:
        print("因为没有获取到章节，程序退出。")
        return
        
    # 测试只抓前 5 章
    all_corpus_data = []
    
    for i, (title, url) in enumerate(chapters):
        chapter_data = scrape_chapter(title, url)
        all_corpus_data.extend(chapter_data)
        time.sleep(2) # 增加了一点休息时间，更安全
        
    if all_corpus_data:
        output_filename = 'syosetu_sample.jsonl'
        print(f"\n抓取结束！准备写入文件 {output_filename} ...")
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            for item in all_corpus_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
        print(f"🎉 成功保存了 {len(all_corpus_data)} 条语料到 {output_filename}！")
    else:
        print("抓取到了章节，但是没提取到内容。")

if __name__ == "__main__":
    main()