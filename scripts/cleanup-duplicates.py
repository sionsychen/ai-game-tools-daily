#!/usr/bin/env python3
"""
日报语义查重清理工具 - v6 (双引擎验证)
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

REPO_DIR = Path("/root/.openclaw/workspace/ai-game-tools-daily")
POSTS_DIR = REPO_DIR / "_posts"

STOPWORDS = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
             'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
             'could', 'should', 'may', 'might', 'can', 'to', 'of', 'in', 
             'for', 'on', 'with', 'at', 'by', 'from', 'as', 'and', 'but', 
             'if', 'or', 'not', 'no', 'this', 'that', 'these', 'those', 
             'i', 'we', 'you', 'he', 'she', 'it', 'they', 'them', 'their'}

ACTION_SYNONYMS = {
    'ban': ['ban', 'bans', 'banned', 'banning', 'prohibit', 'prohibits', 'prohibited',
            'block', 'blocks', 'blocked', 'restrict', 'restricts', 'restricted',
            'forbid', 'forbids', 'forbidden', 'prevent', 'prevents', 'prevented'],
    'launch': ['launch', 'launches', 'launched', 'release', 'releases', 'released',
               'introduce', 'introduces', 'introduced', 'debut', 'debuted', 'unveil', 'unveils'],
    'acquire': ['acquire', 'acquires', 'acquired', 'buy', 'buys', 'bought', 
                'purchase', 'purchases', 'purchased', 'merge', 'merges', 'merged'],
    'update': ['update', 'updates', 'updated', 'upgrade', 'upgrades', 'upgraded',
               'improve', 'improves', 'improved', 'enhance', 'enhances', 'enhanced'],
}

WORD_TO_ACTION = {}
for std, syns in ACTION_SYNONYMS.items():
    for s in syns:
        WORD_TO_ACTION[s] = std

CORE_ENTITIES = {
    'engines': ['godot', 'unity', 'unreal', 'steam', 'nintendo', 'sony', 'microsoft', 
                'xbox', 'playstation', 'epic', 'valve', 'roblox', 'minecraft'],
    'ai': ['ai', 'artificial', 'intelligence', 'machine', 'learning', 'neural', 
           'model', 'llm', 'generative', 'gpt', 'claude', 'deepseek'],
    'code': ['code', 'coding', 'contribution', 'contributions', 'submit', 
              'submission', 'pull', 'request', 'repository', 'commit'],
}

def extract_articles_from_post(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    articles = []
    sections = re.split(r'\n#{2,3} ', content)
    
    for section in sections[1:]:
        lines = section.split('\n')
        section_title = lines[0].strip()
        
        skip_titles = ['summary', 'articles', '📰 ai game tools daily', 'today']
        if section_title.lower() in skip_titles or any(s in section_title.lower() for s in skip_titles):
            continue
        
        body = '\n'.join(lines[1:])
        
        url_match = re.search(r'\*\*sourceUrl:\*\*\s*(https?://[^\s\n]+)', body)
        if not url_match:
            url_match = re.search(r'sourceUrl:\s*(https?://[^\s\n]+)', body)
        url = url_match.group(1) if url_match else ''
        
        article_title = ''
        title_match = re.search(r'- \*\*title:\*\*\s*(.+?)(?:\n|$)', body)
        if title_match:
            article_title = title_match.group(1).strip()
        
        if not article_title:
            article_title = section_title
        
        summary = ''
        summary_match = re.search(r'\*\*summary:\*\* (.+?)(?:\n\*\*summary_zh|\n\*\*category|\n---)', body, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
        
        full_text = article_title + ' ' + summary[:500]
        
        articles.append({
            'title': article_title or section_title,
            'url': url,
            'content': full_text
        })
    
    return articles

def semantic_fingerprint(text):
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    keywords = [w for w in words if w not in STOPWORDS and len(w) >= 2]
    
    features = []
    word_counts = {}
    for w in keywords:
        word_counts[w] = word_counts.get(w, 0) + 1
    for word, count in word_counts.items():
        weight = min(count, 3)
        features.extend([word] * weight)
    for i in range(len(keywords) - 1):
        features.append(f"{keywords[i]}_{keywords[i+1]}")
    for i in range(len(keywords) - 2):
        features.append(f"{keywords[i]}_{keywords[i+1]}_{keywords[i+2]}")
    
    engines = ['godot', 'unity', 'unreal', 'steam', 'nintendo', 'sony', 'microsoft', 
               'xbox', 'playstation', 'epic', 'valve', 'roblox', 'minecraft']
    ai_terms = ['ai', 'artificial', 'intelligence', 'machine', 'learning', 'neural', 
                'model', 'llm', 'generative', 'gpt', 'claude', 'deepseek']
    code_terms = ['code', 'coding', 'contribution', 'contributions', 'submit', 
                  'submission', 'pull', 'request', 'repository', 'commit']
    
    found_engines = [w for w in keywords if w in engines]
    found_ai = [w for w in keywords if w in ai_terms]
    found_code = [w for w in keywords if w in code_terms]
    
    found_actions = []
    for w in keywords:
        if w in WORD_TO_ACTION:
            found_actions.append(WORD_TO_ACTION[w])
    found_actions = list(set(found_actions))
    
    for word in found_engines:
        features.append(f"ENGINE_{word}")
    for word in found_ai:
        features.append(f"AI_{word}")
    for word in found_actions:
        features.append(f"ACTION_{word}")
    for word in found_code:
        features.append(f"CODE_{word}")
    
    for e in found_engines:
        for a in found_ai:
            features.append(f"EVENT_{e}_{a}")
        for a in found_actions:
            features.append(f"EVENT_{e}_{a}")
        for c in found_code:
            features.append(f"EVENT_{e}_{c}")
    for a in found_ai:
        for c in found_code:
            features.append(f"EVENT_{a}_{c}")
        for act in found_actions:
            features.append(f"EVENT_{a}_{act}")
    
    return ' '.join(sorted(features))

def extract_event_signature(text):
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    keywords = [w for w in words if w not in STOPWORDS]
    
    engines = [w for w in keywords if w in CORE_ENTITIES['engines']]
    ai = [w for w in keywords if w in CORE_ENTITIES['ai']]
    code = [w for w in keywords if w in CORE_ENTITIES['code']]
    
    actions = []
    for w in keywords:
        if w in WORD_TO_ACTION:
            actions.append(WORD_TO_ACTION[w])
    actions = list(set(actions))
    
    features = []
    
    for e in engines:
        features.append(f'ENG_{e}')
    for a in ai:
        features.append(f'AI_{a}')
    for c in code:
        features.append(f'CODE_{c}')
    for a in actions:
        features.append(f'ACT_{a}')
    
    for e in engines:
        for a in ai:
            features.append(f'EVT_{e}_{a}')
        for c in code:
            features.append(f'EVT_{e}_{c}')
        for a in actions:
            features.append(f'EVT_{e}_{a}')
    for a in ai:
        for c in code:
            features.append(f'EVT_{a}_{c}')
        for act in actions:
            features.append(f'EVT_{a}_{act}')
    
    for e in engines:
        for a in ai:
            for c in code:
                features.append(f'TRI_{e}_{a}_{c}')
    
    return ' '.join(sorted(features))

def semantic_similarity(fp1, fp2):
    set1 = set(fp1.split())
    set2 = set(fp2.split())
    
    unigrams1 = {f for f in set1 if '_' not in f}
    bigrams1 = {f for f in set1 if '_' in f and f.count('_') == 1}
    trigrams1 = {f for f in set1 if f.count('_') == 2 and not f.startswith('EVENT_')}
    events1 = {f for f in set1 if f.startswith('EVENT_')}
    signatures1 = {f for f in set1 if f.startswith(('ENGINE_', 'AI_', 'ACTION_', 'CODE_'))}
    
    unigrams2 = {f for f in set2 if '_' not in f}
    bigrams2 = {f for f in set2 if '_' in f and f.count('_') == 1}
    trigrams2 = {f for f in set2 if f.count('_') == 2 and not f.startswith('EVENT_')}
    events2 = {f for f in set2 if f.startswith('EVENT_')}
    signatures2 = {f for f in set2 if f.startswith(('ENGINE_', 'AI_', 'ACTION_', 'CODE_'))}
    
    weighted_intersection = (
        len(unigrams1 & unigrams2) * 1 +
        len(bigrams1 & bigrams2) * 3 +
        len(trigrams1 & trigrams2) * 5 +
        len(signatures1 & signatures2) * 8 +
        len(events1 & events2) * 15
    )
    
    weighted_union = (
        len(unigrams1 | unigrams2) * 1 +
        len(bigrams1 | bigrams2) * 3 +
        len(trigrams1 | trigrams2) * 5 +
        len(signatures1 | signatures2) * 8 +
        len(events1 | events2) * 15
    )
    
    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0

def event_similarity(sig1, sig2):
    set1 = set(sig1.split())
    set2 = set(sig2.split())
    
    tri1 = {f for f in set1 if f.startswith('TRI_')}
    tri2 = {f for f in set2 if f.startswith('TRI_')}
    
    evt1 = {f for f in set1 if f.startswith('EVT_')}
    evt2 = {f for f in set2 if f.startswith('EVT_')}
    
    single1 = {f for f in set1 if f.startswith(('ENG_', 'AI_', 'CODE_', 'ACT_'))}
    single2 = {f for f in set2 if f.startswith(('ENG_', 'AI_', 'CODE_', 'ACT_'))}
    
    weighted_intersection = (
        len(single1 & single2) * 2 +
        len(evt1 & evt2) * 10 +
        len(tri1 & tri2) * 30
    )
    
    weighted_union = (
        len(single1 | single2) * 2 +
        len(evt1 | evt2) * 10 +
        len(tri1 | tri2) * 30
    )
    
    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0

def scan_duplicates(semantic_threshold=0.65, event_threshold=0.80, hybrid_semantic=0.30):
    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    all_articles = []
    
    for post_file in sorted(POSTS_DIR.glob('*.md')):
        date_str = post_file.stem.replace('-daily', '')
        if date_str < cutoff:
            continue
        
        articles = extract_articles_from_post(post_file)
        for art in articles:
            all_articles.append({
                'date': date_str,
                'file': post_file,
                'title': art['title'],
                'url': art['url'],
                'content': art['content']
            })
    
    print(f"扫描到 {len(all_articles)} 篇文章（过去30天）")
    print()
    
    duplicates = []
    fingerprints = {}
    event_signatures = {}
    
    for i, art1 in enumerate(all_articles):
        fp1 = semantic_fingerprint(art1['content'])
        sig1 = extract_event_signature(art1['content'])
        fingerprints[i] = fp1
        event_signatures[i] = sig1
        
        for j, art2 in enumerate(all_articles):
            if i >= j:
                continue
            
            fp2 = fingerprints.get(j)
            sig2 = event_signatures.get(j)
            if not fp2:
                fp2 = semantic_fingerprint(art2['content'])
                fingerprints[j] = fp2
            if not sig2:
                sig2 = extract_event_signature(art2['content'])
                event_signatures[j] = sig2
            
            if len(set(fp1.split())) < 8 or len(set(fp2.split())) < 8:
                continue
            
            sem_sim = semantic_similarity(fp1, fp2)
            evt_sim = event_similarity(sig1, sig2)
            
            is_duplicate = (
                sem_sim >= semantic_threshold or
                (sem_sim >= hybrid_semantic and evt_sim >= event_threshold)
            )
            
            if is_duplicate:
                duplicates.append({
                    'art1': art1,
                    'art2': art2,
                    'similarity': sem_sim,
                    'event_similarity': evt_sim
                })
    
    return duplicates

def delete_duplicates(duplicates, dry_run=False):
    """删除重复文章，每组只保留较早的一篇"""
    # 按日期排序，保留每组中较早的文章
    to_delete = []
    kept = []
    
    for dup in duplicates:
        art1 = dup['art1']
        art2 = dup['art2']
        
        # 保留较早的，删除较晚的
        if art1['date'] <= art2['date']:
            keep, delete = art1, art2
        else:
            keep, delete = art2, art1
        
        to_delete.append(delete)
        kept.append(keep)
    
    # 去重（同一篇文章可能在多个组中被标记）
    seen = set()
    unique_delete = []
    for art in to_delete:
        key = (art['date'], art['title'], art['url'])
        if key not in seen:
            seen.add(key)
            unique_delete.append(art)
    
    print(f"{'[试运行] ' if dry_run else ''}计划删除 {len(unique_delete)} 篇重复文章，保留 {len(kept)} 篇")
    print()
    
    for art in unique_delete:
        print(f"  删除: [{art['date']}] {art['title'][:60]}...")
    
    if dry_run:
        return unique_delete
    
    # 实际删除：从文件中移除对应文章
    deleted_count = 0
    for art in unique_delete:
        filepath = art['file']
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 尝试多种匹配模式找到文章 section
        # 模式1: ### 标题\n...--- (标准格式)
        # 模式2: ## 标题\n...--- (有时用 ##)
        
        title = art['title'].strip()
        
        # 先尝试精确匹配标题
        patterns = [
            # 标准格式: ### Title\n...---\n
            rf'\n###\s+{re.escape(title)}\s*\n.*?(?=\n###\s|\n---\s*\n|$)',
            # 宽松: 包含标题关键词
            rf'\n###\s+[^\n]*{re.escape(title[:40])}[^\n]*\n.*?(?=\n###\s|\n---\s*\n|$)',
            # 有时用 ## 开头
            rf'\n##\s+{re.escape(title)}\s*\n.*?(?=\n##\s|\n---\s*\n|$)',
        ]
        
        # 如果标题有编号如 "Article 3:"，尝试匹配后面的部分
        if 'Article' in title:
            article_num = re.search(r'Article\s+\d+[:\s]*(.+)', title, re.IGNORECASE)
            if article_num:
                real_title = article_num.group(1).strip()
                patterns.insert(0, rf'\n###\s+[^\n]*{re.escape(real_title[:40])}[^\n]*\n.*?(?=\n###\s|\n---\s*\n|$)')
        
        found = False
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                # 删除匹配到的部分，包括前面的换行
                start = match.start()
                # 如果前面是 ---\n，也一起删除
                if start >= 4 and content[start-4:start] == '---\n':
                    start = start - 4
                content = content[:start] + content[match.end():]
                found = True
                break
        
        if found and content != original_content:
            # 清理多余的空行和分隔符
            content = re.sub(r'\n{4,}', '\n\n\n', content)
            content = re.sub(r'---\n\n---', '---', content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            deleted_count += 1
            print(f"  ✅ 已删除: [{art['date']}] {art['title'][:50]}...")
        else:
            print(f"  ⚠️ 未找到: [{art['date']}] {art['title'][:50]}...")
    
    print()
    print(f"✅ 成功删除 {deleted_count} 篇重复文章")
    return unique_delete

def main(dry_run=False):
    print("=" * 70)
    print("日报语义查重清理 (双引擎验证)")
    print("=" * 70)
    print()
    
    duplicates = scan_duplicates(semantic_threshold=0.65, event_threshold=0.80, hybrid_semantic=0.30)
    
    if not duplicates:
        print("✅ 未发现重复文章")
        return
    
    print(f"⚠️ 发现 {len(duplicates)} 组重复文章：")
    print()
    
    for dup in duplicates:
        print(f"语义相似度: {dup['similarity']:.2f} | 事件相似度: {dup['event_similarity']:.2f}")
        print(f"  [{dup['art1']['date']}] {dup['art1']['title'][:60]}...")
        print(f"      URL: {dup['art1']['url'][:60]}...")
        print(f"  [{dup['art2']['date']}] {dup['art2']['title'][:60]}...")
        print(f"      URL: {dup['art2']['url'][:60]}...")
        print()
    
    # 删除重复
    print("-" * 70)
    delete_duplicates(duplicates, dry_run=dry_run)

if __name__ == "__main__":
    import sys
    dry_run = '--dry-run' in sys.argv
    main(dry_run=dry_run)
