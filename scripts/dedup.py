#!/usr/bin/env python3
"""
清理日报中的重复文章
策略：保留每个URL最早出现的日期，删除后续重复
"""

import re
from pathlib import Path
from collections import defaultdict
import json

REPO_DIR = Path("/root/.openclaw/workspace/ai-game-tools-daily")
POSTS_DIR = REPO_DIR / "_posts"

def extract_url_from_line(line):
    """从一行中提取URL"""
    match = re.search(r'https?://[^\s\'"\n\)]+', line)
    if match:
        url = match.group(0).rstrip('"').rstrip("'").rstrip(')')
        return url
    return None

def find_duplicates():
    """找出所有跨日期重复的URL"""
    url_to_dates = defaultdict(list)  # url -> [dates]
    url_to_files = {}  # url -> {date: filename}
    
    for post_file in sorted(POSTS_DIR.glob('2026-*.md')):
        date = post_file.stem.split('-daily')[0]
        content = post_file.read_text()
        
        for line in content.split('\n'):
            if 'sourceurl' in line.lower():
                url = extract_url_from_line(line)
                if url:
                    url_to_dates[url].append(date)
                    if url not in url_to_files:
                        url_to_files[url] = {}
                    url_to_files[url][date] = post_file.name
    
    # 找出跨日期重复
    duplicates = {}  # url -> {keep_date: str, remove_dates: [str]}
    for url, dates in url_to_dates.items():
        unique_dates = sorted(set(dates))
        if len(unique_dates) > 1:
            duplicates[url] = {
                'keep_date': unique_dates[0],
                'remove_dates': unique_dates[1:]
            }
    
    return duplicates, url_to_files

def remove_article_by_url(filename, target_url):
    """从文件中删除包含指定URL的文章"""
    filepath = POSTS_DIR / filename
    content = filepath.read_text()
    lines = content.split('\n')
    
    # 找到包含目标URL的行号
    target_line = -1
    for i, line in enumerate(lines):
        if 'sourceurl' in line.lower():
            url = extract_url_from_line(line)
            if url == target_url:
                target_line = i
                break
    
    if target_line == -1:
        print(f"  警告: 在 {filename} 中未找到URL: {target_url[:60]}...")
        return False
    
    # 找到文章开头（向上查找 ### 或 ## 开头的行）
    article_start = 0
    for i in range(target_line, -1, -1):
        line = lines[i].strip()
        if line.startswith('### ') or line.startswith('## Article') or line.startswith('## ') or line.startswith('**title'):
            article_start = i
            break
    
    # 找到文章结束（下一篇文章开头或文件末尾）
    article_end = len(lines)
    for i in range(target_line + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith('### ') or line.startswith('## Article') or (line.startswith('## ') and not line.startswith('## Articles')) or line.startswith('**title'):
            article_end = i
            break
    
    # 删除文章
    new_lines = lines[:article_start] + lines[article_end:]
    
    # 清理连续空行
    cleaned = []
    prev_empty = False
    for line in new_lines:
        if line.strip() == '':
            if not prev_empty:
                cleaned.append(line)
            prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False
    
    filepath.write_text('\n'.join(cleaned))
    return True

def rebuild_used_urls(duplicates, url_to_files):
    """重建 used_urls.json"""
    used_urls = {}
    
    # 收集所有保留的URL
    for post_file in sorted(POSTS_DIR.glob('2026-*.md')):
        date = post_file.stem.split('-daily')[0]
        content = post_file.read_text()
        
        for line in content.split('\n'):
            if 'sourceurl' in line.lower():
                url = extract_url_from_line(line)
                if url:
                    if date not in used_urls:
                        used_urls[date] = []
                    if url not in used_urls[date]:
                        used_urls[date].append(url)
    
    # 保存到两个位置
    (REPO_DIR / "_data").mkdir(exist_ok=True)
    
    with open(REPO_DIR / "used_urls.json", 'w') as f:
        json.dump(used_urls, f, indent=2)
    
    with open(REPO_DIR / "_data" / "used_urls.json", 'w') as f:
        json.dump(used_urls, f, indent=2)
    
    total_urls = sum(len(urls) for urls in used_urls.values())
    print(f"\n已重建 used_urls.json")
    print(f"  共 {len(used_urls)} 天，{total_urls} 个URL")

def main():
    print("=== 日报重复文章清理 ===\n")
    
    duplicates, url_to_files = find_duplicates()
    
    if not duplicates:
        print("未发现跨日期重复的文章！")
        return
    
    print(f"发现 {len(duplicates)} 个URL跨日期重复:\n")
    
    for url, info in sorted(duplicates.items(), key=lambda x: -len(x[1]['remove_dates'])):
        print(f"{url[:80]}...")
        print(f"  保留: {info['keep_date']}")
        print(f"  删除: {', '.join(info['remove_dates'])}")
    
    # 执行删除
    print("\n\n开始删除重复文章...")
    total_removed = 0
    
    for url, info in duplicates.items():
        for remove_date in info['remove_dates']:
            filename = url_to_files[url].get(remove_date)
            if filename:
                if remove_article_by_url(filename, url):
                    print(f"  ✓ 从 {filename} 删除重复")
                    total_removed += 1
                else:
                    print(f"  ✗ 从 {filename} 删除失败")
            else:
                print(f"  ✗ 找不到 {remove_date} 的文件 for {url[:60]}...")
    
    print(f"\n共删除 {total_removed} 个重复文章")
    
    # 重建 used_urls.json
    print("\n重建 used_urls.json...")
    rebuild_used_urls(duplicates, url_to_files)
    
    print("\n=== 清理完成 ===")

if __name__ == "__main__":
    main()
