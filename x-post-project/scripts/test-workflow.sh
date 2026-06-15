#!/bin/bash

# X帖子创作发布工作流测试脚本

set -e

echo "=========================================="
echo "X帖子创作发布工作流测试"
echo "=========================================="

# 创建项目目录
PROJECT_DIR="/Users/piaoxian/x-post-project"
mkdir -p "$PROJECT_DIR/posts"
mkdir -p "$PROJECT_DIR/logs"

# 测试1: 获取热门分类
echo ""
echo "测试1: 获取热门分类"
echo "------------------------------------------"

# 使用之前获取的热门分类数据
cat > "$PROJECT_DIR/trending-categories.json" << 'EOF'
{
  "fetched_at": "2026-05-25T13:39:34.891538",
  "source": "xtrends.in",
  "country": "united-states",
  "categories": [
    {
      "headline": "#TheBoys",
      "url": "https://twitter.com/search?q=%23TheBoys",
      "category": "trending",
      "postCount": null,
      "timeAgo": "just now"
    },
    {
      "headline": "#LOLFanFest2026LIVE",
      "url": "https://twitter.com/search?q=%23LOLFanFest2026LIVE",
      "category": "trending",
      "postCount": null,
      "timeAgo": "just now"
    },
    {
      "headline": "Harden",
      "url": "https://twitter.com/search?q=Harden",
      "category": "trending",
      "postCount": null,
      "timeAgo": "just now"
    },
    {
      "headline": "Congratulations Scott",
      "url": "https://twitter.com/search?q=Congratulations+Scott",
      "category": "trending",
      "postCount": null,
      "timeAgo": "just now"
    },
    {
      "headline": "Brunson",
      "url": "https://twitter.com/search?q=Brunson",
      "category": "trending",
      "postCount": null,
      "timeAgo": "just now"
    }
  ]
}
EOF

echo "✓ 热门分类已保存到: $PROJECT_DIR/trending-categories.json"

# 显示获取的热门分类
echo ""
echo "获取的热门分类:"
cat "$PROJECT_DIR/trending-categories.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for i, cat in enumerate(data['categories'], 1):
    print(f\"  {i}. {cat['headline']}\")
"

# 测试2: 获取热门帖子（使用第一个分类）
echo ""
echo "测试2: 获取热门帖子"
echo "------------------------------------------"
FIRST_CATEGORY=$(cat "$PROJECT_DIR/trending-categories.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['categories'][0]['headline'].replace('#', ''))
")

# 创建分类目录
CATEGORY_SLUG=$(echo "$FIRST_CATEGORY" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
mkdir -p "$PROJECT_DIR/posts/$CATEGORY_SLUG"

# 获取热门帖子
python3 "$PROJECT_DIR/scripts/fetch-posts.py" "$FIRST_CATEGORY" 3 > "$PROJECT_DIR/posts/$CATEGORY_SLUG/category-posts.json"
echo "✓ 热门帖子已保存到: $PROJECT_DIR/posts/$CATEGORY_SLUG/category-posts.json"

# 显示获取的帖子
echo ""
echo "获取的热门帖子:"
cat "$PROJECT_DIR/posts/$CATEGORY_SLUG/category-posts.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for i, post in enumerate(data['posts'], 1):
    content = post['content'][:80] + '...' if len(post['content']) > 80 else post['content']
    print(f\"  {i}. {content}\")
    print(f\"     URL: {post['url']}\")
"

# 测试3: 模拟仿写和人性化处理
echo ""
echo "测试3: 模拟仿写和人性化处理"
echo "------------------------------------------"

# 创建仿写内容
cat > "$PROJECT_DIR/posts/$CATEGORY_SLUG/01-post-rewritten.md" << 'EOF'
# 仿写帖子内容

这是一个测试帖子，基于热门话题进行仿写创作。

原始话题的热度很高，我们可以借鉴其成功的元素，同时创作出独特的内容。

关键要点：
1. 保持话题的相关性
2. 使用吸引人的标题
3. 包含有价值的信息
4. 鼓励用户互动

让我们一起探索这个热门话题的更多可能性！
EOF

echo "✓ 仿写内容已保存到: $PROJECT_DIR/posts/$CATEGORY_SLUG/01-post-rewritten.md"

# 创建人性化处理后的内容
cat > "$PROJECT_DIR/posts/$CATEGORY_SLUG/02-post-humanized.md" << 'EOF'
# 人性化处理后的内容

看到这个话题火了，我也来凑个热闹。

说实话，这个话题确实挺有意思的。我观察了一下，发现几个关键点：

首先，大家对这个话题的关注度很高。其次，讨论的角度很多样。最后，有很多有价值的观点在分享。

我觉得这个话题之所以能火，主要是因为它触及了大家的共同兴趣。如果你也感兴趣，不妨参与讨论，分享你的看法。
EOF

echo "✓ 人性化处理后的内容已保存到: $PROJECT_DIR/posts/$CATEGORY_SLUG/02-post-humanized.md"

# 测试4: 字数检查
echo ""
echo "测试4: 字数检查"
echo "------------------------------------------"

CONTENT=$(cat "$PROJECT_DIR/posts/$CATEGORY_SLUG/02-post-humanized.md")
CHAR_COUNT=${#CONTENT}

echo "内容字符数: $CHAR_COUNT"
echo "限制: 280字符（普通用户）/ 10,000字符（Premium用户）"

if [ $CHAR_COUNT -gt 280 ]; then
    echo "⚠️  内容超过280字符限制，需要精简"
else
    echo "✓ 内容符合280字符限制"
fi

# 创建最终发布内容
cp "$PROJECT_DIR/posts/$CATEGORY_SLUG/02-post-humanized.md" "$PROJECT_DIR/posts/$CATEGORY_SLUG/03-post-final.md"
echo "✓ 最终发布内容已保存到: $PROJECT_DIR/posts/$CATEGORY_SLUG/03-post-final.md"

# 测试5: 创建搜索关键词
echo ""
echo "测试5: 创建搜索关键词"
echo "------------------------------------------"

mkdir -p "$PROJECT_DIR/posts/$CATEGORY_SLUG/images"

cat > "$PROJECT_DIR/posts/$CATEGORY_SLUG/images/search-keyword.md" << EOF
# 图片搜索关键词

原始话题: $FIRST_CATEGORY
搜索关键词: $FIRST_CATEGORY trending social media
图片类型: 横版图片
用途: X帖子配图
EOF

echo "✓ 搜索关键词已保存到: $PROJECT_DIR/posts/$CATEGORY_SLUG/images/search-keyword.md"

# 测试6: 创建工作流状态
echo ""
echo "测试6: 创建工作流状态"
echo "------------------------------------------"

cat > "$PROJECT_DIR/workflow-state.json" << EOF
{
  "workflow_id": "x-post-test-$(date +%Y%m%d-%H%M%S)",
  "current_step": 7,
  "total_steps": 8,
  "status": "in_progress",
  "completed_steps": [1, 2, 3, 4, 5, 6],
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project_dir": "$PROJECT_DIR",
  "category": "$FIRST_CATEGORY",
  "category_slug": "$CATEGORY_SLUG"
}
EOF

echo "✓ 工作流状态已保存到: $PROJECT_DIR/workflow-state.json"

# 完成测试
echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "项目目录: $PROJECT_DIR"
echo "分类目录: $PROJECT_DIR/posts/$CATEGORY_SLUG"
echo ""
echo "下一步:"
echo "1. 配置Pexels API Key（可选）"
echo "2. 运行: /zcf:x-post-workflow"
echo ""
echo "注意: 定时发布功能需要用户手动确认"
