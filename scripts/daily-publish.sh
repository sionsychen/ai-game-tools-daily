#!/bin/bash
# 发布AI游戏工具日报（git commit + push）
# 纯脚本，不调用AI

set -euo pipefail

export PATH="/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

REPO_DIR="/root/.openclaw/workspace/ai-game-tools-daily"
LOG_FILE="/root/.openclaw/workspace/logs/ai-game-tools-daily.log"
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
TODAY=$(date '+%Y-%m-%d')

cd "$REPO_DIR"

echo "[$DATETIME] ===== daily-publish.sh start =====" >> "$LOG_FILE"

# 加载 GitHub Token
if [ -f /root/.openclaw/workspace/.env.github ]; then
    set -a
    source /root/.openclaw/workspace/.env.github
    set +a
fi
GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "[$DATETIME] ERROR: GITHUB_TOKEN not set" >> "$LOG_FILE"
    exit 1
fi

# 检查是否有变更
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "[$DATETIME] Changes detected, proceeding to commit/push" >> "$LOG_FILE"
else
    echo "[$DATETIME] No changes to publish" >> "$LOG_FILE"
    echo "[$DATETIME] ===== daily-publish.sh nothing to do =====" >> "$LOG_FILE"
    exit 0
fi

# 配置 git
git config user.name "AI Game Tools Daily" || true
git config user.email "ai-tools@gamedev.tech" || true

# 设置带Token的remote
REMOTE_URL="https://sionsychen:${GITHUB_TOKEN}@github.com/sionsychen/ai-game-tools-daily.git"
git remote set-url origin "$REMOTE_URL"

cleanup_remote() {
    git remote set-url origin "https://github.com/sionsychen/ai-game-tools-daily.git" || true
}
trap cleanup_remote EXIT

# 提交并推送
git add _posts/_data/
git commit -m "Publish daily: ${TODAY}" || true
git pull origin main --rebase || true
git push origin main

echo "[$DATETIME] GitHub push completed" >> "$LOG_FILE"

# 简单验证GitHub Pages是否更新（最多等60秒）
SITE_URL="https://sionsychen.github.io/ai-game-tools-daily/"
echo "[$DATETIME] Verifying site..." >> "$LOG_FILE"

for i in {1..6}; do
    sleep 10
    # 检查页面中是否包含今天的日期（2026-04-12 或 April 12）
    if curl -s "$SITE_URL" | grep -qE "${TODAY}|$(date '+%B %d')"; then
        echo "[$DATETIME] Site verified: today's date found" >> "$LOG_FILE"
        echo "[$DATETIME] ===== daily-publish.sh success =====" >> "$LOG_FILE"
        exit 0
    fi
    echo "[$DATETIME] Site not yet updated, retry $i/6..." >> "$LOG_FILE"
done

echo "[$DATETIME] WARNING: Site verification timed out, but push succeeded" >> "$LOG_FILE"
echo "[$DATETIME] ===== daily-publish.sh success (needs manual verify) =====" >> "$LOG_FILE"
exit 0
