# Twitter API申请和配置指南

## 申请步骤

### 1. 访问Twitter开发者平台
- 访问 https://developer.twitter.com/
- 使用您的X账号登录

### 2. 申请开发者访问权限
- 点击"Sign up"或"Apply"
- 选择"Essentials"访问级别（免费）
- 填写申请表格：
  - 用途描述：个人内容创作和研究
  - 使用场景：获取热门话题和帖子进行内容分析

### 3. 创建项目
- 在开发者仪表板中点击"Create Project"
- 项目名称：X-Post-Workflow
- 用途选择：Making a bot / Academic research

### 4. 创建应用
- 在项目中创建新应用
- 应用名称：X-Post-App

### 5. 获取API密钥
在应用的"Keys and tokens"页面获取：

**API Key和API Secret**
- 点击"Regenerate"生成新的API Key
- 保存API Key和API Secret

**Access Token和Access Token Secret**
- 点击"Generate"生成Access Token
- 保存Access Token和Access Token Secret

**Bearer Token**
- 点击"Generate"生成Bearer Token
- 保存Bearer Token

## 配置环境变量

### 方法1：临时设置（当前会话）
```bash
export TWITTER_API_KEY='your_api_key_here'
export TWITTER_API_SECRET='your_api_secret_here'
export TWITTER_ACCESS_TOKEN='your_access_token_here'
export TWITTER_ACCESS_SECRET='your_access_token_secret_here'
export TWITTER_BEARER_TOKEN='your_bearer_token_here'
```

### 方法2：永久设置（添加到shell配置文件）
```bash
# 添加到 ~/.zshrc 或 ~/.bash_profile
cat >> ~/.zshrc << 'EOF'
# Twitter API配置
export TWITTER_API_KEY='your_api_key_here'
export TWITTER_API_SECRET='your_api_secret_here'
export TWITTER_ACCESS_TOKEN='your_access_token_here'
export TWITTER_ACCESS_SECRET='your_access_token_secret_here'
export TWITTER_BEARER_TOKEN='your_bearer_token_here'
EOF

# 重新加载配置
source ~/.zshrc
```

### 方法3：使用env文件
```bash
# 创建env文件
cat > ~/.config/twitter-api.env << 'EOF'
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_token_secret_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
EOF

# 加载env文件
source ~/.config/twitter-api.env
```

## 验证配置

```bash
# 检查环境变量
echo "API Key: $TWITTER_API_KEY"
echo "Bearer Token: $TWITTER_BEARER_TOKEN"

# 测试API连接
python3 << 'EOF'
import tweepy
import os

# 获取环境变量
api_key = os.environ.get('TWITTER_API_KEY')
api_secret = os.environ.get('TWITTER_API_SECRET')
access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
access_token_secret = os.environ.get('TWITTER_ACCESS_SECRET')
bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')

# 检查配置
if all([api_key, api_secret, access_token, access_token_secret, bearer_token]):
    print("✅ 所有API密钥已配置")
    
    # 创建客户端
    client = tweepy.Client(bearer_token=bearer_token)
    
    # 测试搜索
    try:
        tweets = client.search_recent_tweets(query="AI lang:en", max_results=10)
        print(f"✅ API连接成功，获取到 {len(tweets.data)} 条推文")
    except Exception as e:
        print(f"❌ API连接失败: {e}")
else:
    print("❌ 缺少API密钥")
    print("请配置以下环境变量：")
    print("  TWITTER_API_KEY")
    print("  TWITTER_API_SECRET")
    print("  TWITTER_ACCESS_TOKEN")
    print("  TWITTER_ACCESS_SECRET")
    print("  TWITTER_BEARER_TOKEN")
EOF
```

## 使用示例

### 搜索推文
```python
import tweepy
import os

# 创建客户端
client = tweepy.Client(bearer_token=os.environ.get('TWITTER_BEARER_TOKEN'))

# 搜索AI相关推文
tweets = client.search_recent_tweets(
    query="AI lang:en min_faves:100",
    max_results=10,
    tweet_fields=['created_at', 'public_metrics', 'author_id']
)

for tweet in tweets.data:
    print(f"Tweet: {tweet.text[:100]}...")
    print(f"Likes: {tweet.public_metrics['like_count']}")
    print(f"Retweets: {tweet.public_metrics['retweet_count']}")
    print("---")
```

### 获取用户推文
```python
import tweepy
import os

# 创建客户端
client = tweepy.Client(bearer_token=os.environ.get('TWITTER_BEARER_TOKEN'))

# 获取用户推文
user = client.get_user(username="elonmusk")
tweets = client.get_users_tweets(
    id=user.data.id,
    max_results=10,
    tweet_fields=['created_at', 'public_metrics']
)

for tweet in tweets.data:
    print(f"Tweet: {tweet.text[:100]}...")
    print(f"Likes: {tweet.public_metrics['like_count']}")
    print("---")
```

## 常见问题

### Q: API访问被拒绝
A: 检查API密钥是否正确，以及是否有足够的API访问权限

### Q: 请求频率限制
A: Twitter API有请求频率限制，免费账户每15分钟15次请求

### Q: 数据不完整
A: 免费账户可能无法获取所有字段，需要升级到付费计划

## 下一步

配置完成后，可以：
1. 运行工作流测试脚本
2. 开始使用X帖子创作发布工作流
3. 自定义搜索关键词和参数

---

配置完成后，请告知我，我将更新工作流脚本以使用Twitter API。
