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
USED_URLS_FILE_ROOT = REPO_DIR / "used_urls.json"

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

# 语义查重配置
SEMANTIC_THRESHOLD = 0.55  # 相似度阈值（针对事件签名优化）
SEMANTIC_HISTORY_DAYS = 30   # 历史数据天数
SEMANTIC_FINGERPRINTS_FILE = REPO_DIR / "_data" / "semantic_fingerprints.json"

# 领域关键词库（用于事件签名提取）
DOMAIN_KEYWORDS = {
    'engines': ['godot', 'unity', 'unreal', 'cryengine', 'source'],
    'ai_terms': ['ai', 'artificial', 'intelligence', 'generative', 'llm'],
    'code_terms': ['code', 'coding', 'programming', 'script', 'repository', 'commit', 'submission', 'contribution'],
    'actions': ['ban', 'bans', 'prohibit', 'prohibits', 'block', 'blocks', 'allow', 'allows', 'release', 'releases']
}
STOPWORDS = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
             'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
             'would', 'could', 'should', 'may', 'might', 'must', 'shall',
             'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for',
             'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
             'before', 'after', 'above', 'below', 'between', 'under', 'again',
             'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
             'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
             'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
             'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while', 'this',
             'that', 'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our',
             'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
             'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it',
             'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'}

def semantic_fingerprint(text):
    """提取事件签名：引擎 + AI + 代码 + 动作"""
    text = text.lower()
    words = set(re.findall(r'\b\w+\b', text))
    
    signature = []
    for category, keywords in DOMAIN_KEYWORDS.items():
        matches = [w for w in keywords if w in words]
        if matches:
            signature.extend(matches)
    
    return ' '.join(sorted(set(signature)))

def similarity_score(fp1, fp2):
    """计算加权Jaccard相似度：引擎x3 + AIx2 + 其他x1"""
    set1 = set(fp1.split())
    set2 = set(fp2.split())
    
    # 分类特征
    engines1 = set1 & {'godot', 'unity', 'unreal', 'cryengine', 'source'}
    engines2 = set2 & {'godot', 'unity', 'unreal', 'cryengine', 'source'}
    ai1 = set1 & {'ai', 'artificial', 'intelligence', 'generative', 'llm'}
    ai2 = set2 & {'ai', 'artificial', 'intelligence', 'generative', 'llm'}
    other1 = set1 - engines1 - ai1
    other2 = set2 - engines2 - ai2
    
    # 加权匹配
    engine_match = len(engines1 & engines2) * 3
    ai_match = len(ai1 & ai2) * 2
    other_match = len(other1 & other2)
    
    weighted_intersection = engine_match + ai_match + other_match
    
    # 并集
    all_engines = engines1 | engines2
    all_ai = ai1 | ai2
    all_other = other1 | other2
    weighted_union = len(all_engines) * 3 + len(all_ai) * 2 + len(all_other)
    
    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0

def load_semantic_fingerprints():
    """加载历史语义指纹（30天内）"""
    if not SEMANTIC_FINGERPRINTS_FILE.exists():
        return []
    
    try:
        with open(SEMANTIC_FINGERPRINTS_FILE, 'r') as f:
            data = json.load(f)
        
        cutoff = (datetime.now() - timedelta(days=SEMANTIC_HISTORY_DAYS)).strftime('%Y-%m-%d')
        
        fingerprints = []
        for date_str, fps in data.items():
            if date_str >= cutoff and isinstance(fps, list):
                fingerprints.extend(fps)
        
        return fingerprints
    except:
        return []

def save_semantic_fingerprint(fingerprint, date_str):
    """保存语义指纹"""
    SEMANTIC_FINGERPRINTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if SEMANTIC_FINGERPRINTS_FILE.exists():
        try:
            with open(SEMANTIC_FINGERPRINTS_FILE, 'r') as f:
                data = json.load(f)
        except:
            pass
    
    if date_str not in data:
        data[date_str] = []
    
    data[date_str].append(fingerprint)
    
    with open(SEMANTIC_FINGERPRINTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def semantic_filter(articles, threshold=SEMANTIC_THRESHOLD):
    """语义去重：与30天内历史文章比较"""
    history_fingerprints = load_semantic_fingerprints()
    
    filtered = []
    for art in articles:
        fp = semantic_fingerprint(art['title'] + ' ' + art.get('desc', ''))
        
        is_duplicate = False
        for hist_fp in history_fingerprints:
            if similarity_score(fp, hist_fp) >= threshold:
                log(f"语义去重: '{art['title'][:50]}...' 与历史文章相似度超过{threshold}")
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered.append(art)
            history_fingerprints.append(fp)
    
    return filtered

# 分类关键词
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

def load_used_urls(days=365):
    """加载已使用的URL - 加载所有历史数据防止重复"""
    # 优先从根目录加载（兼容旧路径）
    if USED_URLS_FILE_ROOT.exists():
        try:
            with open(USED_URLS_FILE_ROOT, 'r') as f:
                data = json.load(f)
            # 如果是旧格式（按日期分组的dict）
            if isinstance(data, dict):
                return data
            # 如果是新格式（简单列表）
            elif isinstance(data, list):
                return {"all": data}
        except:
            pass
    
    if USED_URLS_FILE.exists():
        try:
            with open(USED_URLS_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                return {"all": data}
        except:
            pass
    
    return {}

def save_used_urls(data):
    """保存已使用的URL到两个位置"""
    USED_URLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_URLS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    with open(USED_URLS_FILE_ROOT, 'w') as f:
        json.dump(data, f, indent=2)
    log(f"used_urls.json 已更新，共 {sum(len(v) for v in data.values())} 个URL")

def filter_duplicates(articles, days=365):
    """过滤重复文章 - 检查所有历史URL"""
    used_data = load_used_urls(days)
    used_urls = set()
    for urls in used_data.values():
        if isinstance(urls, list):
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
    """生成摘要 - 详细版本（200-400字符）"""
    # 优先使用描述，如果描述太短则基于标题扩展
    base_text = desc if desc else f"探讨{title}相关的技术进展与应用"
    
    # 清理并扩展摘要
    summary = base_text.strip()
    
    # 确保摘要足够详细（至少200字符，最多400字符）
    if len(summary) < 200 and desc:
        # 如果原始描述较短，尝试保留更多内容
        summary = desc[:400].strip()
    
    if len(summary) > 400:
        # 截断到合理长度，尽量在句子边界
        cutoff = summary.rfind('.', 200, 400)
        if cutoff == -1:
            cutoff = summary.rfind(' ', 300, 400)
        if cutoff == -1:
            cutoff = 400
        summary = summary[:cutoff+1].strip()
    
    return summary

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
    
    # 使用 SSH 方式推送
    run_git(['remote', 'set-url', 'origin', 'git@github.com:sionsychen/ai-game-tools-daily.git'])
    
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
        # 恢复为SSH URL
        run_git(['remote', 'set-url', 'origin', 'git@github.com:sionsychen/ai-game-tools-daily.git'], check=False)
    
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
    
    # 过滤重复并限制数量（3-5篇高质量）
    articles = filter_duplicates(articles)
    if not articles:
        log("所有文章已发布过", "WARN")
        return False
    
    # 语义去重（30天历史，阈值0.65）
    articles = semantic_filter(articles)
    if not articles:
        log("所有文章通过语义查重已发布过", "WARN")
        return False
    
    # 限制为最多5篇
    articles = articles[:5]
    
    log(f"使用 {len(articles)} 篇新文章")
    
    articles_info = []
    used_urls_today = []
    processed_articles = []
    
    # 先处理所有文章数据
    for i, art in enumerate(articles[:5], 1):
        category = detect_category(art['title'], art['desc'])
        summary = generate_summary(art['title'], art['desc'])
        
        processed_articles.append({
            'id': f"{date_str}-{i}",
            'title': art['title'],
            'category': category,
            'sourceUrl': art['url'],
            'summary': summary
        })
        
        articles_info.append({
            "title": art['title'],
            "category": category
        })
        used_urls_today.append(art['url'])
    
    # 生成 front matter（包含所有 articles 数据）
    def clean_yaml(s):
        return s.replace('"', '').replace('\n', ' ').strip()
    
    articles_yaml = "\n".join([f"""  - id: "{a['id']}"
    title: "{clean_yaml(a['title'])}"
    category: {a['category']}
    sourceUrl: "{a['sourceUrl']}"
    summary: "{clean_yaml(a['summary'])}""" for a in processed_articles])
    
    # 生成正文内容
    body_content = "\n\n---\n\n".join([f"""## {a['title']}

<div class="article-meta">
  <span class="category-badge tag-{a['category']}">{a['category'].replace('ai-', 'AI ').title()}</span>
</div>

{a['summary']}

<div class="article-footer-link">
  <a href="{a['sourceUrl']}" target="_blank">🔗 Read Original</a>
</div>""" for a in processed_articles])
    
    content = f"""---
layout: post
title: "AI Game Tools Daily - {today.strftime('%B %d, %Y')}"
date: "{date_str} 11:00:00 +0800"
categories: [Daily]
lang: en
permalink: /{today.strftime('%Y/%m/%d')}/daily/
articles:
{articles_yaml}
---

{body_content}


*🐾 Generated by OpenClaw on {today.strftime('%B %d, %Y')}*"""
    
    # 保存文件
    (REPO_DIR / "_posts").mkdir(parents=True, exist_ok=True)
    with open(REPO_DIR / "_posts" / f"{date_str}-daily.md", 'w', encoding='utf-8') as f:
        f.write(content)
    log("文件已保存")
    
    # 记录语义指纹
    for art in articles[:5]:
        fp = semantic_fingerprint(art['title'] + ' ' + art.get('desc', ''))
        save_semantic_fingerprint(fp, date_str)
    
    log(f"已保存 {len(articles[:5])} 个语义指纹")
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
