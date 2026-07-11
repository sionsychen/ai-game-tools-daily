#!/bin/bash
# 修复后的日报生成脚本 - 增加错误处理和重试机制

export PATH="/root/.nvm/versions/node/v22.22.2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:$PATH"
export HOME="/root"

# 加载环境变量
if [ -f /root/.openclaw/workspace/.env.github ]; then
    set -a
    source /root/.openclaw/workspace/.env.github
    set +a
fi

REPO_DIR="/root/.openclaw/workspace/ai-game-tools-daily"
LOG_FILE="/root/.openclaw/workspace/logs/ai-game-tools-daily.log"
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
TODAY=$(date '+%Y-%m-%d')

# 重试函数
retry_with_backoff() {
    local max_retries=3
    local retry_count=0
    local wait_time=5
    
    while [ $retry_count -lt $max_retries ]; do
        if "$@"; then
            return 0
        fi
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            echo "[$DATETIME] 重试 $retry_count/$max_retries，等待 ${wait_time}s..." >> "$LOG_FILE"
            sleep $wait_time
            wait_time=$((wait_time * 2))
        fi
    done
    return 1
}

echo "[$DATETIME] ===== 修复版日报生成脚本启动 =====" >> "$LOG_FILE"

cd "$REPO_DIR"

# 检查并创建必要的目录
mkdir -p "$REPO_DIR/_posts"
mkdir -p "$REPO_DIR/_data"

# 检查 used_urls.json 文件位置（兼容新旧路径）
if [ -f "$REPO_DIR/used_urls.json" ]; then
    echo "[$DATETIME] 发现旧路径 used_urls.json，迁移到 _data/ 目录" >> "$LOG_FILE"
    cp "$REPO_DIR/used_urls.json" "$REPO_DIR/_data/used_urls.json"
fi

# 确保 _data/used_urls.json 存在
if [ ! -f "$REPO_DIR/_data/used_urls.json" ]; then
    echo "[$DATETIME] 创建空的 used_urls.json" >> "$LOG_FILE"
    echo "[]" > "$REPO_DIR/_data/used_urls.json"
fi

# 运行Python脚本生成日报
if [ -f "$REPO_DIR/scripts/daily-scraper.py" ]; then
    echo "[$DATETIME] 运行 daily-scraper.py..." >> "$LOG_FILE"
    python3 "$REPO_DIR/scripts/daily-scraper.py" >> "$LOG_FILE" 2>&1
    SCRAPER_EXIT=$?
    
    if [ $SCRAPER_EXIT -ne 0 ]; then
        echo "[$DATETIME] ERROR: daily-scraper.py 失败 (exit: $SCRAPER_EXIT)" >> "$LOG_FILE"
        # 即使失败也尝试推送已生成的内容
    fi
else
    echo "[$DATETIME] WARNING: daily-scraper.py 不存在，跳过生成步骤" >> "$LOG_FILE"
fi

# 检查今日文件是否生成
TODAY_FILE="$REPO_DIR/_posts/${TODAY}-daily.md"
if [ ! -f "$TODAY_FILE" ]; then
    echo "[$DATETIME] ERROR: 今日日报文件未生成: $TODAY_FILE" >> "$LOG_FILE"
    exit 1
fi

echo "[$DATETIME] 今日日报文件已生成: $TODAY_FILE" >> "$LOG_FILE"

# Git 提交和推送
if [ -n "$(git status --porcelain)" ]; then
    echo "[$DATETIME] 检测到变更，准备提交..." >> "$LOG_FILE"
    
    git config user.name "AI Game Tools Daily" || true
    git config user.email "ai-tools@gamedev.tech" || true
    
    # 使用 SSH 而非 HTTPS（如果已配置）
    if git remote get-url origin | grep -q "git@github.com"; then
        echo "[$DATETIME] 使用 SSH 推送" >> "$LOG_FILE"
    else
        # 配置 HTTPS with token
        if [ -n "${GITHUB_TOKEN:-}" ]; then
            REMOTE_URL="https://sionsychen:${GITHUB_TOKEN}@github.com/sionsychen/ai-game-tools-daily.git"
            git remote set-url origin "$REMOTE_URL"
            echo "[$DATETIME] 使用 HTTPS with token 推送" >> "$LOG_FILE"
        else
            echo "[$DATETIME] ERROR: GITHUB_TOKEN 未设置" >> "$LOG_FILE"
            exit 1
        fi
    fi
    
    # 添加文件并提交
    git add _posts/ _data/ used_urls.json 2>/dev/null || true
    
    # 提交（如果失败也不退出）
    git commit -m "Publish daily: ${TODAY}" >> "$LOG_FILE" 2>&1 || true
    
    # 推送（带重试）
    echo "[$DATETIME] 推送到 GitHub..." >> "$LOG_FILE"
    if retry_with_backoff git push origin main; then
        echo "[$DATETIME] GitHub 推送成功" >> "$LOG_FILE"
    else
        echo "[$DATETIME] ERROR: GitHub 推送失败，但本地文件已保存" >> "$LOG_FILE"
        # 不退出，因为本地文件已生成
    fi
    
    # 恢复 remote URL（如果是临时设置的）
    if [ -n "${GITHUB_TOKEN:-}" ] && ! git remote get-url origin | grep -q "git@github.com"; then
        git remote set-url origin "https://github.com/sionsychen/ai-game-tools-daily.git" 2>/dev/null || true
    fi
else
    echo "[$DATETIME] 无变更需要提交" >> "$LOG_FILE"
fi

echo "[$DATETIME] ===== 修复版日报生成脚本完成 =====" >> "$LOG_FILE"
exit 0