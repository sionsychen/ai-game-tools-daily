#!/bin/bash
# AI Game Tools Daily - Daily Report Wrapper

export PATH="/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

# Load environment
if [ -f /root/.openclaw/workspace/.env.github ]; then
    export $(grep -v '^#' /root/.openclaw/workspace/.env.github | xargs)
fi

# API Keys
export BRAVE_API_KEY="BSAQlRCKyEt1sjkQvQOjne1Rp-t45J6"

LOG_FILE="/root/.openclaw/workspace/logs/ai-game-tools-daily.log"
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATETIME] =========================================" >> "$LOG_FILE"
echo "[$DATETIME] Starting AI Game Tools Daily scraper..." >> "$LOG_FILE"

# Run scraper
cd /root/.openclaw/workspace/ai-game-tools-daily
python3 scripts/daily-scraper.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "[$DATETIME] Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "[$DATETIME] =========================================" >> "$LOG_FILE"

exit $EXIT_CODE
