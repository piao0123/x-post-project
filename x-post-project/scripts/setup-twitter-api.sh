#!/bin/bash

# Twitter API 自动配置脚本
# 使用方法: ./setup-twitter-api.sh

set -e

echo "=== Twitter API 自动配置脚本 ==="
echo ""

# 检查是否已有配置
if [ -n "$TWITTER_BEARER_TOKEN" ]; then
    echo "✅ Twitter API已配置"
    echo "Bearer Token: ${TWITTER_BEARER_TOKEN:0:20}..."
    exit 0
fi

echo "正在配置Twitter API..."
echo ""

# 交互式获取API密钥
read -p "请输入TWITTER_API_KEY: " api_key
read -p "请输入TWITTER_API_SECRET: " api_secret
read -p "请输入TWITTER_ACCESS_TOKEN: " access_token
read -p "请输入TWITTER_ACCESS_SECRET: " access_secret
read -p "请输入TWITTER_BEARER_TOKEN: " bearer_token

# 验证输入
if [ -z "$api_key" ] || [ -z "$api_secret" ] || [ -z "$access_token" ] || [ -z "$access_secret" ] || [ -z "$bearer_token" ]; then
    echo "❌ 错误：所有字段都是必填的"
    exit 1
fi

# 创建配置目录
config_dir="$HOME/.config/twitter-api"
mkdir -p "$config_dir"

# 写入配置文件
cat > "$config_dir/api-keys.env" << EOF
TWITTER_API_KEY=$api_key
TWITTER_API_SECRET=$api_secret
TWITTER_ACCESS_TOKEN=$access_token
TWITTER_ACCESS_SECRET=$access_secret
TWITTER_BEARER_TOKEN=$bearer_token
EOF

# 设置文件权限（仅用户可读写）
chmod 600 "$config_dir/api-keys.env"

echo "✅ 配置文件已保存到: $config_dir/api-keys.env"
echo ""

# 加载到当前环境
export TWITTER_API_KEY="$api_key"
export TWITTER_API_SECRET="$api_secret"
export TWITTER_ACCESS_TOKEN="$access_token"
export TWITTER_ACCESS_SECRET="$access_secret"
export TWITTER_BEARER_TOKEN="$bearer_token"

# 测试连接
echo "正在测试Twitter API连接..."
python3 << 'EOF'
import tweepy
import os

api_key = os.environ.get('TWITTER_API_KEY')
api_secret = os.environ.get('TWITTER_API_SECRET')
access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
access_token_secret = os.environ.get('TWITTER_ACCESS_SECRET')
bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')

if all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
    try:
        client = tweepy.Client(bearer_token=bearer_token)
        tweets = client.search_recent_tweets(query="AI lang:en", max_results=5)
        print(f"✅ API连接成功！获取到 {len(tweets.data)} 条推文")
    except Exception as e:
        print(f"⚠️ API连接测试失败: {e}")
else:
    print("❌ 缺少API密钥")
EOF

echo ""
echo "=== 配置完成 ==="
echo "下一步："
echo "1. 运行工作流测试: /zcf:x-post-workflow"
echo "2. 或手动测试: bird search 'AI lang:en' -n 5 --json"