#!/usr/bin/env python3
"""
AI Game Tools Daily - Content Scraper
Daily automation for AI game development tool news
"""

import os
import subprocess
import requests
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

# Config
REPO_DIR = Path("/root/.openclaw/workspace/ai-game-tools-daily")
LOG_FILE = Path("/root/.openclaw/workspace/logs/ai-game-tools-daily.log")
USED_URLS_FILE = REPO_DIR / "_data" / "used_urls.json"
ENV_FILE = Path("/root/.openclaw/workspace/.env.github")

# API Keys
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Load from env file if not set
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith('GITHUB_TOKEN=') and not GITHUB_TOKEN:
                    GITHUB_TOKEN = line.split('=', 1)[1].strip()
    except Exception:
        pass

# Search queries focused on AI tools for game development
SEARCH_QUERIES = [
    # AI Art Tools
    "site:80.lv AI art generation game textures",
    "site:gamedeveloper.com generative AI art tools 2025",
    "AI texture generation game development",
    "Stable Diffusion game asset workflow",
    
    # AI Coding
    "site:github.blog Copilot game development",
    "AI coding assistant Unity Unreal Engine",
    "ChatGPT shader code generation",
    "AI script generation game development",
    
    # AI Audio
    "AI sound effect generation game audio",
    "generative AI music game soundtrack",
    "ElevenLabs voice AI game dialogue",
    "AI voice synthesis game characters",
    
    # AI Animation
    "AI motion capture game animation",
    "generative AI character animation",
    "AI facial animation game development",
    
    # AI Level Design
    "procedural generation AI level design",
    "AI dungeon generator game development",
    "machine learning level generation",
    
    # Industry News
    "site:80.lv AI tools game industry",
    "site:gamedeveloper.com artificial intelligence gaming",
    "Unity AI features 2025",
    "Unreal Engine AI tools updates",
]

# Category mapping
CATEGORY_KEYWORDS = {
    'ai-art': ['art', 'texture', 'image', 'sprite', 'material', 'concept art', 'stable diffusion', 'midjourney', 'dall-e'],
    'ai-coding': ['code', 'coding', 'script', 'github copilot', 'shader', 'programming', 'developer assistant'],
    'ai-audio': ['audio', 'sound', 'music', 'voice', 'sfx', 'elevenlabs', 'audio generation'],
    'ai-animation': ['animation', 'motion', 'mocap', 'facial animation', 'character animation'],
    'ai-level-design': ['level', 'procedural', 'generation', 'dungeon', 'world building', 'map generation'],
    'ai-testing': ['test', 'qa', 'bug', 'automation', 'quality assurance'],
    'industry-news': ['industry', 'news', 'trends', 'market', 'business', 'investment'],
}


def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{ts}] [{level}] {msg}"
    print(log_line)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')


def send_feishu_message(content):
    """Send notification to Feishu"""
    try:
        result = subprocess.run(
            ['openclaw', 'message', 'send',
             '--channel', 'feishu',
             '--target', 'ou_6bf225e82b5c7a7e1872429fee274e3b',
             '--message', content],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except Exception as e:
        log(f"Feishu message failed: {e}", "ERROR")
        return False


def search_articles():
    """Search for AI game development articles"""
    if not BRAVE_API_KEY:
        log("BRAVE_API_KEY not set", "ERROR")
        return []
    
    articles = []
    seen_urls = set()
    
    for query in SEARCH_QUERIES:
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY
            }
            params = {"q": query, "count": 5, "freshness": "pw"}
            
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("web", {}).get("results", [])
                
                for r in results:
                    url_str = r.get("url", "")
                    if url_str in seen_urls:
                        continue
                    seen_urls.add(url_str)
                    
                    # Filter low quality sources
                    if any(domain in url_str for domain in ['forum', 'reddit', 'discord']):
                        continue
                    
                    articles.append({
                        "title": r.get("title", "").split(" - ")[0].split(" | ")[0],
                        "url": url_str,
                        "desc": r.get("description", ""),
                    })
                    
                if len(articles) >= 15:
                    break
                    
        except Exception as e:
            log(f"Search error: {e}", "ERROR")
    
    return articles[:15]


def fetch_with_browser(url):
    """Fetch article content using agent-browser"""
    try:
        result = subprocess.run(
            ['agent-browser', 'open', url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            subprocess.run(['agent-browser', 'wait', '3000'], 
                          capture_output=True, timeout=10)
            
            result = subprocess.run(
                ['agent-browser', 'eval', 'document.body.innerText'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                text = result.stdout.strip()
                text = re.sub(r'\s+', ' ', text)
                
                if len(text) < 500:
                    text = None
                else:
                    text = text[:5000] if len(text) > 5000 else text
                    
                subprocess.run(['agent-browser', 'close'], capture_output=True)
                return text
        
        subprocess.run(['agent-browser', 'close'], capture_output=True)
        
        # Fallback to requests
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            text = re.sub(r'<[^>]+>', ' ', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:4000] if len(text) > 4000 else text
            
    except Exception as e:
        log(f"Fetch error: {e}", "WARN")
        subprocess.run(['agent-browser', 'close'], capture_output=True)
    return None


def categorize_article(title, desc, content):
    """Determine article category based on content"""
    text = (title + " " + desc + " " + (content or "")).lower()
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[category] = score
    
    # Return category with highest score, default to industry-news
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'industry-news'


def extract_tags(title, desc, category):
    """Extract relevant tags from content"""
    text = (title + " " + desc).lower()
    tags = []
    
    tag_mappings = {
        'unity': 'Unity',
        'unreal': 'Unreal Engine',
        'ue5': 'UE5',
        'blender': 'Blender',
        'stable diffusion': 'Stable Diffusion',
        'midjourney': 'Midjourney',
        'dalle': 'DALL-E',
        'chatgpt': 'ChatGPT',
        'github copilot': 'GitHub Copilot',
        'elevenlabs': 'ElevenLabs',
        'shader': 'Shaders',
        'texture': 'Textures',
        'animation': 'Animation',
        'procedural': 'Procedural',
        'generative': 'Generative AI',
    }
    
    for keyword, tag in tag_mappings.items():
        if keyword in text:
            tags.append(tag)
    
    # Add category as tag if not already included
    category_tag = category.replace('ai-', '').replace('-', ' ').title()
    if category_tag not in tags:
        tags.append(category_tag)
    
    return list(dict.fromkeys(tags))[:3]


def generate_summary(content):
    """Generate summary from article content"""
    if not content:
        return "Article about AI tools for game development. Click to read more."
    
    # Clean and extract sentences
    text = re.sub(r'\s+', ' ', content).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    meaningful = []
    for s in sentences:
        s = s.strip()
        if 40 < len(s) < 250:
            if s.count('{') < 2 and s.count('}') < 2:
                # Check for game/AI keywords
                if any(word in s.lower() for word in ['ai', 'game', 'tool', 'unity', 'unreal', 'generate', 'automation']):
                    meaningful.append(s)
        if len(meaningful) >= 2:
            break
    
    if meaningful:
        summary = ' '.join(meaningful)
        return summary[:250] + '...' if len(summary) > 250 else summary
    
    return text[:200] + '...' if len(text) > 200 else text


def load_used_urls():
    """Load previously used URLs"""
    if not USED_URLS_FILE.exists():
        return {}
    try:
        with open(USED_URLS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_used_urls(data):
    """Save used URLs"""
    USED_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_URLS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def push_to_github(date_str):
    """Push changes to GitHub"""
    if not GITHUB_TOKEN:
        log("GITHUB_TOKEN not set", "ERROR")
        return False
    
    try:
        subprocess.run(['git', 'config', 'user.name', 'AI Game Tools Daily'], 
                      cwd=REPO_DIR, check=False)
        subprocess.run(['git', 'config', 'user.email', 'daily@ai-game-tools.dev'], 
                      cwd=REPO_DIR, check=False)
        
        remote_url = f"https://sionsychen:{GITHUB_TOKEN}@github.com/sionsychen/ai-game-tools-daily.git"
        subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], 
                      cwd=REPO_DIR, check=False)
        
        subprocess.run(['git', 'add', '.'], cwd=REPO_DIR, check=False)
        subprocess.run(['git', 'commit', '-m', f'Update: {date_str}'], 
                      cwd=REPO_DIR, check=False)
        subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'], 
                      cwd=REPO_DIR, check=False)
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                               cwd=REPO_DIR, capture_output=True)
        
        subprocess.run(['git', 'remote', 'set-url', 'origin', 
                       'https://github.com/sionsychen/ai-game-tools-daily.git'], 
                      cwd=REPO_DIR, check=False)
        
        return result.returncode == 0
    except Exception as e:
        log(f"Git push failed: {e}", "ERROR")
        return False


def simple_translate(title):
    """Translate title to Chinese for Feishu"""
    phrases = [
        ("AI", "AI"),
        ("Artificial Intelligence", "人工智能"),
        ("Generative", "生成式"),
        ("Game Development", "游戏开发"),
        ("Unity", "Unity"),
        ("Unreal Engine", "虚幻引擎"),
        ("Tutorial", "教程"),
        ("Guide", "指南"),
        ("Best Practices", "最佳实践"),
        ("Tools", "工具"),
        ("Animation", "动画"),
        ("Audio", "音频"),
        ("Texture", "材质"),
        ("Shader", "着色器"),
    ]
    
    result = title
    for en, zh in phrases:
        if en.lower() in title.lower():
            result = re.sub(re.escape(en), zh, result, flags=re.IGNORECASE)
    
    return result.strip()


def generate():
    """Main generation function"""
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    log(f"===== AI Game Tools Daily: {date_str} =====")
    
    # Search for articles
    log("Searching articles...")
    articles = search_articles()
    
    if not articles:
        log("No articles found", "ERROR")
        return False
    
    # Filter duplicates
    used_urls = load_used_urls()
    all_used = set()
    for urls in used_urls.values():
        all_used.update(urls)
    
    new_articles = []
    for art in articles:
        if art['url'] not in all_used:
            new_articles.append(art)
    
    if len(new_articles) < 3:
        log(f"Not enough new articles ({len(new_articles)})", "WARN")
        return False
    
    log(f"Processing {len(new_articles[:5])} articles...")
    
    # Process articles
    processed = []
    for art in new_articles[:5]:
        log(f"  Processing: {art['title'][:50]}...")
        
        content = fetch_with_browser(art['url'])
        category = categorize_article(art['title'], art['desc'], content)
        tags = extract_tags(art['title'], art['desc'], category)
        summary = generate_summary(content)
        
        processed.append({
            'id': f"{date_str}-{len(processed)+1}",
            'title': art['title'],
            'date': date_str,
            'category': category,
            'tags': tags,
            'sourceUrl': art['url'],
            'sourceName': art['url'].split('/')[2].replace('www.', ''),
            'summary': summary,
        })
    
    # Generate markdown post
    md_content = f"""---
layout: post
title: "AI Game Tools Daily - {today.strftime('%B %d, %Y')}"
date: "{date_str} 11:00:00 +0800"
categories: [Daily]
lang: en
permalink: /{today.strftime('%Y/%m/%d')}/daily/
---

"""
    
    for art in processed:
        tag_html = '\n  '.join([f'<span class="article-category">#{t}</span>' for t in art['tags']])
        md_content += f"""## {art['title']}

<div class="article-meta">
  {tag_html}
</div>

{art['summary']}

<div class="article-footer-link">
  <a href="{art['sourceUrl']}" target="_blank" class="source-link">🔗 Read Original</a>
</div>

---

"""
    
    md_content += f"\n*🐾 Generated by OpenClaw on {today.strftime('%B %d, %Y')}*"
    
    # Save files
    posts_dir = REPO_DIR / "_posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    with open(posts_dir / f"{date_str}-daily.md", 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    # Update posts.json
    data_file = REPO_DIR / "src" / "data" / "posts.json"
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
    except Exception:
        data = {"version": "1.0", "posts": []}
    
    data['posts'].insert(0, {
        "date": date_str,
        "articles": processed
    })
    
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    log("Files saved")
    
    # Push to GitHub
    push_success = push_to_github(date_str)
    
    # Send Feishu notification
    weekday_cn = {'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三',
                  'Thursday': '周四', 'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日'}[today.strftime('%A')]
    
    article_list = []
    for i, art in enumerate(processed[:3], 1):
        tags_str = ' '.join([f'#{t}' for t in art['tags']])
        title_zh = simple_translate(art['title'])
        article_list.append(f"**{i}.** {title_zh} {tags_str}\n  {art['summary'][:100]}...\n  👉 [Read]({art['sourceUrl']})")
    
    msg = f"""🤖 **AI Game Tools Daily**

📅 {date_str} · {weekday_cn}

---

🎯 **今日头条**

{chr(10).join(article_list)}

---

🔗 [View Full Report](https://sionsychen.github.io/ai-game-tools-daily)

{'✅ 网站已同步更新' if push_success else '⚠️ 网站同步状态未知'}

---

💡 **内容方向**: AI Art · AI Coding · AI Audio · AI Animation · AI Level Design

🐾 -- 小黑"""
    
    send_feishu_message(msg)
    
    # Save used URLs
    if date_str not in used_urls:
        used_urls[date_str] = []
    for art in processed:
        used_urls[date_str].append(art['sourceUrl'])
    save_used_urls(used_urls)
    
    log(f"===== Complete: {len(processed)} articles =====")
    return push_success


if __name__ == "__main__":
    import sys
    success = generate()
    sys.exit(0 if success else 1)
