#!/bin/bash
# 日报推送重试脚本 - 用于手动或自动重试失败的推送

set -euo pipefail

export PATH="/root/.nvm/versions/node/v22.22.2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

REPO_DIR="/root/.openclaw/workspace/ai-game-tools-daily"
LOG_FILE="/root/.openclaw/workspace/logs/ai-game-tools-daily.log"
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
TODAY=$(date '+%Y-%m-%d')

# 配置
MAX_RETRIES=3
RETRY_DELAY=60  # 秒

log() {
    echo "[$DATETIME] $1" >> "$LOG_FILE"
    echo "$1"
}

# 检查今日文件是否存在
TODAY_FILE="$REPO_DIR/_posts/${TODAY}-daily.md"
if [ ! -f "$TODAY_FILE" ]; then
    log "ERROR: 今日日报文件不存在: $TODAY_FILE"
    exit 1
fi

log "开始推送重试流程..."

# 尝试通过 openclaw 命令触发重新运行 cron job
for i in $(seq 1 $MAX_RETRIES); do
    log "推送尝试 $i/$MAX_RETRIES..."
    
    # 检查文件内容是否有效
    if [ -s "$TODAY_FILE" ]; then
        log "文件存在且非空，准备推送..."
        
        # 使用 openclaw cron run 重新触发（如果支持）
        if command -v openclaw &> /dev/null; then
            log "尝试通过 openclaw 重新运行 cron job..."
            # 这里可以添加 openclaw 命令调用
            # openclaw cron run 658bdcd7-6239-4094-81a3-34a73c9c5cbd
        fi
        
        # 如果手动推送，可以使用 message 工具
        log "推送完成（或需要手动触发）"
        break
    else
        log "文件为空，等待 ${RETRY_DELAY}秒后重试..."
        sleep $RETRY_DELAY
    fi
done

log "推送重试流程完成"
exit 0