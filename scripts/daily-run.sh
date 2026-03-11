#!/bin/bash
# AI游戏工具日报生成脚本 - 包装器

export PATH="/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

# 加载环境变量
if [ -f /root/.openclaw/workspace/.env.github ]; then
    set -a
    source /root/.openclaw/workspace/.env.github
    set +a
    export GITHUB_TOKEN
    export BRAVE_API_KEY
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
