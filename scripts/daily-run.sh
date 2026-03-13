#!/bin/bash
# AI游戏工具日报生成脚本 - 包装器

export PATH="/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

# 加载环境变量（如果存在）
if [ -f /root/.openclaw/workspace/.env.github ]; then
    set -a
    source /root/.openclaw/workspace/.env.github
    set +a
fi

# 硬编码API Keys作为后备（确保始终可用）
export BRAVE_API_KEY="${BRAVE_API_KEY:-BSAQlRCKyEt1sjkQvQOjne1Rp-t45J6}"
export GITHUB_TOKEN="${GITHUB_TOKEN:-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}"

# 验证
if [ -z "$GITHUB_TOKEN" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: GITHUB_TOKEN 未设置" >&2
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] GITHUB_TOKEN: 已设置 ${GITHUB_TOKEN:0:10}..."
fi

if [ -z "$BRAVE_API_KEY" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: BRAVE_API_KEY 未设置" >&2
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BRAVE_API_KEY: 已设置 ${BRAVE_API_KEY:0:10}..."
fi

LOG_FILE="/root/.openclaw/workspace/logs/ai-game-tools-daily.log"
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATETIME] =========================================" >> "$LOG_FILE"
echo "[$DATETIME] 启动AI游戏工具日报生成..." >> "$LOG_FILE"

# 运行Python脚本
python3 /root/.openclaw/workspace/ai-game-tools-daily/scripts/daily-scraper.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "[$DATETIME] 脚本执行完成，退出码: $EXIT_CODE" >> "$LOG_FILE"
echo "[$DATETIME] =========================================" >> "$LOG_FILE"

exit $EXIT_CODE
