#!/bin/bash
# 生成AI游戏工具日报内容（调用OpenClaw Agent）
# 注意：只做内容生成，不涉及git操作

set -euo pipefail

export PATH="/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

REPO_DIR="/root/.openclaw/workspace/ai-game-tools-daily"
LOG_FILE="/root/.openclaw/workspace/logs/ai-game-tools-daily.log"
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
TODAY=$(date '+%Y-%m-%d')

echo "[$DATETIME] ===== daily-generate.sh start =====" >> "$LOG_FILE"

# 组装 Prompt
PROMPT=$(cat <<'EOF'
Generate today's bilingual AI Game Tools Daily update.

=== TASK SCOPE (CRITICAL) ===
ONLY generate content and save files. Do NOT run any git commands.

=== CONTENT QUALITY STANDARDS ===
EXCLUDE low-value sources:
- AWS/Amazon/Azure/Google official product pages
- Unity/Unreal official announcements
- Generic marketing materials without independent analysis
- Press releases without commentary

INCLUDE high-value sources:
- Industry analysis reports (Hartmann Capital, research firms)
- Tech news with analysis (GDC coverage, industry trends)
- Developer-focused reviews and tool comparisons
- Independent analysis and commentary

Quantity guideline: 3-4 high-quality articles > 5 mediocre articles

=== STEP 1: SEARCH ===
Search AI game tools news from past 7 days using web_search.

=== STEP 2: FILTER & DE-DUPLICATE ===
Read /root/.openclaw/workspace/ai-game-tools-daily/_data/used_urls.json
Exclude any URLs already used in the past 30 days.
Exclude Unity/Unreal official announcements.

=== STEP 3: GENERATE BILINGUAL ARTICLES ===
Categories: ai-trends, ai-npc, ai-tools, ai-art, ai-code, ai-audio, ai-animation, cloud-gaming

For each article produce:
- title: English title
- title_zh: Chinese title
- summary: English summary (1-2 sentences)
- summary_zh: Chinese summary
- sourceUrl: Unique URL (never reuse existing URLs)
- category: One of the valid categories above

Then write a Today's Summary paragraph in Chinese synthesizing the key insights.

=== STEP 4: SAVE FILES ===
Write to:
- _posts/YYYY-MM-DD-daily.md (use layout: new_post, include bilingual front matter and section-based HTML body)
- Update _data/used_urls.json with today's new URLs

CRITICAL RULES:
1. UNIQUE sourceUrl for each article
2. Bilingual content (Chinese + English)
3. Use layout: new_post
4. No git commands
EOF
)

# 调用 OpenClaw Agent 执行生成任务
echo "[$DATETIME] Calling OpenClaw agent for content generation..." >> "$LOG_FILE"

if openclaw agent run --cwd "$REPO_DIR" --timeout-seconds 600 --message "$PROMPT" >> "$LOG_FILE" 2>&1; then
    echo "[$DATETIME] Content generation completed" >> "$LOG_FILE"
    # 验证文件是否生成
    if [ -f "$REPO_DIR/_posts/${TODAY}-daily.md" ]; then
        echo "[$DATETIME] Verified: ${TODAY}-daily.md exists" >> "$LOG_FILE"
        echo "[$DATETIME] ===== daily-generate.sh success =====" >> "$LOG_FILE"
        exit 0
    else
        echo "[$DATETIME] ERROR: ${TODAY}-daily.md not found after generation" >> "$LOG_FILE"
        echo "[$DATETIME] ===== daily-generate.sh failed =====" >> "$LOG_FILE"
        exit 1
    fi
else
    echo "[$DATETIME] ERROR: Agent run failed" >> "$LOG_FILE"
    echo "[$DATETIME] ===== daily-generate.sh failed =====" >> "$LOG_FILE"
    exit 1
fi
