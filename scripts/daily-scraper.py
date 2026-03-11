#!/usr/bin/env python3
"""
AI游戏工具日报生成器

功能：
- 搜索AI游戏工具相关新闻
- 生成Jekyll格式的日报
- 推送到GitHub
- 发送飞书通知
"""

import os
import subprocess
import requests
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# 配置
REPO_DIR = Path("/root/.openclaw/workspace/ai-game-tools-daily")
LOG_FILE = Path("/root/.openclaw/workspace/logs/ai-game-tools-daily.log")
USED_URLS_FILE = REPO_DIR / "_data" / "used_urls.json"

# API Keys
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

# 搜索查询 - AI游戏工具相关
SEARCH_QUERIES = [
    "AI game development tools 2025",
    "AI art generation game assets",
    "AI coding assistant game development",
    "AI audio generation game sound",
    "AI animation game characters",
    "procedural generation AI game",
    "Unity AI tools Muse",
    "Unreal Engine AI plugins",
    "Midjourney game concept art",
    "Stable Diffusion game textures",
]

# 分类关键词
CATEGORY_KEYWORDS = {
    "ai-art": ["art", "image", "texture", "concept", "sprite", "midjourney", "stable diffusion", "dalle"],
    "ai-code": ["code", "script", "programming", "copilot", "shader", "autocomplete"],
    "ai-audio": ["audio", "sound", "music", "voice", "sfx", "speech"],
    "ai-animation": ["animation", "motion", "rigging", "facial", "mocap"],
    "ai-3d": ["3d", "model", "mesh", "geometry", "procedural"],
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{ts}] [{level}] {msg}"
    print(log_line)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')

def run_git(args, check=True):
    try:
        result = subprocess.run(
            ['git'] + args, cwd=REPO_DIR,
            capture_output=True, text=True, timeout=60
        )
        if check and result.returncode != 0:
            log(f"Git失败: {' '.join(args)} - {result.stderr}", "ERROR")
            return None
        return result
    except Exception as e:
        log(f"Git异常: {e}", "ERROR")
        return None

def search_articles():
    """使用Brave Search搜索文章"""
    if not BRAVE_API_KEY:
        log("BRAVE_API_KEY未设置", "ERROR")
        return []
    
    articles = []
    seen_urls = set()
    
    for query in SEARCH_QUERIES[:3]:  # 限制查询数量
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": BRAVE_API_KEY
            }
            params = {
                "q": query,
                "count": 5,
                "text_decorations": False,
                "search_lang": "en"
            }
            
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                log(f"搜索失败: {resp.status_code}", "WARN")
                continue
            
            data = resp.json()
            for result in data.get("web", {}).get("results", []):
                url = result.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                articles.append({
                    "title": result.get("title", ""),
                    "url": url,
                    "desc": result.get("description", ""),
                })
            
            log(f"搜索 '{query[:30]}...' 找到 {len(data.get('web', {}).get('results', []))} 条")
            
        except Exception as e:
            log(f"搜索异常: {e}", "WARN")
    
    return articles

def load_used_urls(days=30):
    """加载已使用的URL"""
    if not USED_URLS_FILE.exists():
        return {}
    try:
        with open(USED_URLS_FILE, 'r') as f:
            data = json.load(f)
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return {k: v for k, v in data.items() if k >= cutoff}
    except:
        return {}

def save_used_urls(data):
    """保存已使用的URL"""
    USED_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_URLS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def filter_duplicates(articles, days=30):
    """过滤重复文章"""
    used_data = load_used_urls(days)
    used_urls = set()
    for urls in used_data.values():
        used_urls.update(urls)
    
    filtered = []
    for art in articles:
        url = art.get('url', '').split('#')[0].rstrip('/')
        if url not in used_urls:
            filtered.append(art)
    
    return filtered

def detect_category(title, desc):
    """检测文章分类"""
    text = (title + " " + desc).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return cat
    return "ai-tools"

def generate_summary(title, desc):
    """生成摘要"""
    if len(desc) > 150:
        return desc[:150] + "..."
    return desc if desc else f"Article about {title}"

def push_to_github(date_str):
    """推送到GitHub"""
    global GITHUB_TOKEN
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", GITHUB_TOKEN)
    
    if not GITHUB_TOKEN:
        log("GITHUB_TOKEN未设置", "ERROR")
        return False
    
    log("开始GitHub推送...")
    run_git(['config', 'user.name', 'AI Game Tools Daily'], check=False)
    run_git(['config', 'user.email', 'ai-tools@gamedev.tech'], check=False)
    
    # 设置带Token的remote
    remote_url = f"https://sionsychen:{GITHUB_TOKEN}@github.com/sionsychen/ai-game-tools-daily.git"
    run_git(['remote', 'set-url', 'origin', remote_url])
    
    try:
        run_git(['add', '.'])
        run_git(['commit', '-m', f'Publish daily: {date_str}'], check=False)
        run_git(['pull', 'origin', 'main', '--rebase'], check=False)
        result = run_git(['push', 'origin', 'main'])
        if result:
            log("GitHub推送成功")
            return True
    except Exception as e:
        log(f"GitHub推送失败: {e}", "ERROR")
    finally:
        run_git(['remote', 'set-url', 'origin', 'https://github.com/sionsychen/ai-game-tools-daily.git'], check=False)
    
    return False

def send_feishu(articles_info, push_success, date_str):
    """发送飞书通知"""
    try:
        weekday_cn = {'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
                      'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'}[datetime.now().strftime('%A')]
        
        article_list = []
        for i, art in enumerate(articles_info[:3], 1):
            cat_cn = {
                "ai-art": "🎨 AI美术", "ai-code": "💻 AI编程", "ai-audio": "🔊 AI音频",
                "ai-animation": "🎬 AI动画", "ai-3d": "🧊 AI 3D", "ai-tools": "🛠️ AI工具"
            }.get(art['category'], "🛠️ AI工具")
            article_list.append(f"**{i}.** {cat_cn} · {art['title'][:40]}...")
        
        msg = f"""🤖 **AI游戏工具日报**

📅 {date_str} · {weekday_cn}

{chr(10).join(article_list)}

🔗 [查看完整日报](https://sionsychen.github.io/ai-game-tools-daily/)

{'✅ 网站已同步' if push_success else '⚠️ 同步状态未知'}

🐾 -- 小黑"""
        
        subprocess.run([
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', 'ou_6bf225e82b5c7a7e1872429fee274e3b',
            '--message', msg
        ], capture_output=True, timeout=60)
        log("飞书消息已发送")
    except Exception as e:
        log(f"飞书发送异常: {e}", "WARN")

def generate():
    """主生成函数"""
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    log(f"===== AI游戏工具日报: {date_str} =====")
    
    # 搜索文章
    articles = search_articles()
    if not articles:
        log("未找到文章", "ERROR")
        return False
    
    # 过滤重复
    articles = filter_duplicates(articles)
    if not articles:
        log("所有文章已发布过", "WARN")
        return False
    
    log(f"使用 {len(articles)} 篇新文章")
    
    # 生成日报内容
    content = f"""---
layout: post
title: "AI Game Tools Daily - {today.strftime('%B %d, %Y')}"
date: "{date_str} 11:00:00 +0800"
categories: [Daily]
lang: en
permalink: /{today.strftime('%Y/%m/%d')}/daily/
articles:
"""
    
    articles_info = []
    used_urls_today = []
    
    for i, art in enumerate(articles[:5], 1):
        category = detect_category(art['title'], art['desc'])
        summary = generate_summary(art['title'], art['desc'])
        
        content += f"""  - id: "{date_str}-{i}"
    title: "{art['title']}"
    category: {category}
    sourceUrl: "{art['url']}"
---

## {art['title']}

<div class="article-meta">
  <span class="category-badge tag-{category}">{category.replace('ai-', 'AI ').title()}</span>
</div>

{summary}

<div class="article-footer-link">
  <a href="{art['url']}" target="_blank">🔗 Read Original</a>
</div>

---

"""
        articles_info.append({
            "title": art['title'],
            "category": category
        })
        used_urls_today.append(art['url'])
    
    content += f"\n*🐾 Generated by OpenClaw on {today.strftime('%B %d, %Y')}*"
    
    # 保存文件
    (REPO_DIR / "_posts").mkdir(parents=True, exist_ok=True)
    with open(REPO_DIR / "_posts" / f"{date_str}-daily.md", 'w', encoding='utf-8') as f:
        f.write(content)
    log("文件已保存")
    
    # 记录已使用URL
    used_data = load_used_urls()
    used_data[date_str] = used_urls_today
    save_used_urls(used_data)
    
    # 推送到GitHub
    push_success = push_to_github(date_str)
    
    # 发送飞书通知
    send_feishu(articles_info, push_success, date_str)
    
    log("===== 日报生成完成 =====")
    return True

if __name__ == "__main__":
    try:
        generate()
    except Exception as e:
        log(f"生成异常: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
