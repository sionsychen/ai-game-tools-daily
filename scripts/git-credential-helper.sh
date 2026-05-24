#!/bin/bash
# GitHub 凭证辅助脚本

# 从环境变量获取 Token
TOKEN="$GITHUB_TOKEN"

if [ -z "$TOKEN" ]; then
    echo "Error: GITHUB_TOKEN not set" >&2
    exit 1
fi

# 输出凭证
echo "protocol=https"
echo "host=github.com"
echo "username=x-access-token"
echo "password=$TOKEN"
