#!/bin/bash

# X帖子创作发布工作流 - 自动配置脚本

set -e

echo "=========================================="
echo "X帖子创作发布工作流 - 自动配置"
echo "=========================================="

# 创建配置目录
mkdir -p /Users/piaoxian/x-post-project/config

# 方案1：设置Pexels API Key
echo ""
echo "方案1: 设置Pexels API Key"
echo "------------------------------------------"
echo "访问 https://www.pexels.com/api/ 注册获取API Key"
echo ""
read -p "请输入Pexels API Key (或按回车跳过): " api_key

if [ -n "$api_key" ]; then
    # 保存到环境变量
    echo "export PEXELS_API_KEY=\"$api_key\"" >> ~/.zshrc
    export PEXELS_API_KEY="$api_key"
    echo "✓ Pexels API Key 已设置"

    # 创建配置文件
    cat > /Users/piaoxian/x-post-project/config/pexels.json << EOF
{
  "provider": "pexels",
  "api_key": "$api_key",
  "enabled": true
}
EOF
    echo "✓ Pexels配置已保存"
else
    echo "跳过Pexels API Key设置"
fi

# 方案2：配置免费图片网站
echo ""
echo "方案2: 配置免费图片网站"
echo "------------------------------------------"
echo "可用的免费图片网站："
echo "1. Unsplash (https://unsplash.com)"
echo "2. Pixabay (https://pixabay.com)"
echo "3. Pexels (https://pexels.com)"
echo ""

# 创建免费图片网站配置
cat > /Users/piaoxian/x-post-project/config/free-sites.json << 'EOF'
{
  "free_sites": [
    {
      "name": "Unsplash",
      "url": "https://unsplash.com",
      "search_url": "https://unsplash.com/s/photos/",
      "free": true,
      "commercial_use": true
    },
    {
      "name": "Pixabay",
      "url": "https://pixabay.com",
      "search_url": "https://pixabay.com/images/search/",
      "free": true,
      "commercial_use": true
    },
    {
      "name": "Pexels",
      "url": "https://pexels.com",
      "search_url": "https://pexels.com/search/",
      "free": true,
      "commercial_use": true
    }
  ]
}
EOF
echo "✓ 免费图片网站配置已保存"

# 方案3：配置自定义图片
echo ""
echo "方案3: 配置自定义图片"
echo "------------------------------------------"
echo "您可以提供图片URL或本地路径"
echo ""

# 创建自定义图片配置
cat > /Users/piaoxian/x-post-project/config/custom-images.json << 'EOF'
{
  "custom_images": {
    "enabled": true,
    "allow_url": true,
    "allow_local_path": true,
    "supported_formats": ["jpg", "jpeg", "png", "gif", "webp"],
    "max_file_size_mb": 10
  }
}
EOF
echo "✓ 自定义图片配置已保存"

# 验证X认证
echo ""
echo "验证X平台认证..."
if bird check > /dev/null 2>&1; then
    echo "✓ X平台认证正常"
else
    echo "⚠ X平台认证未配置"
    echo "  运行 'bird login' 进行配置"
fi

# 创建主配置文件
cat > /Users/piaoxian/x-post-project/config/main.json << 'EOF'
{
  "workflow": {
    "name": "X帖子创作发布工作流",
    "version": "1.0.0",
    "created_at": "2026-05-25"
  },
  "image_sources": {
    "pexels": {
      "enabled": true,
      "priority": 1
    },
    "free_sites": {
      "enabled": true,
      "priority": 2
    },
    "custom_images": {
      "enabled": true,
      "priority": 3
    }
  },
  "defaults": {
    "country": "united-states",
    "category_count": 10,
    "post_count": 5,
    "image_orientation": "landscape",
    "char_limit_normal": 280,
    "char_limit_premium": 10000
  }
}
EOF
echo "✓ 主配置文件已保存"

# 显示配置完成
echo ""
echo "=========================================="
echo "配置完成"
echo "=========================================="
echo ""
echo "配置文件位置: /Users/piaoxian/x-post-project/config/"
echo ""
echo "下一步："
echo "1. 运行测试验证配置："
echo "   /Users/piaoxian/x-post-project/scripts/test-workflow.sh"
echo ""
echo "2. 启动工作流："
echo "   /zcf:x-post-workflow"
echo ""
echo "3. 查看配置指南："
echo "   /Users/piaoxian/x-post-project/CONFIG-GUIDE.md"
