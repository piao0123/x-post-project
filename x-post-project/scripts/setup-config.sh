#!/bin/bash

# X帖子创作发布工作流 - 配置设置脚本

set -e

echo "=========================================="
echo "X帖子创作发布工作流 - 配置设置"
echo "=========================================="

# 检查现有配置
echo ""
echo "检查现有配置..."
if [ -n "$PEXELS_API_KEY" ]; then
    echo "✓ Pexels API Key 已设置"
    echo "  当前Key: ${PEXELS_API_KEY:0:10}..."
else
    echo "✗ Pexels API Key 未设置"
fi

# 检查bird CLI配置
echo ""
echo "检查X平台认证..."
if bird check > /dev/null 2>&1; then
    echo "✓ X平台认证已配置"
else
    echo "✗ X平台认证未配置"
fi

# 显示配置选项
echo ""
echo "=========================================="
echo "配置选项"
echo "=========================================="
echo ""
echo "请选择配置方案："
echo ""
echo "1. 设置Pexels API Key（推荐）"
echo "   - 免费注册获取API Key"
echo "   - 200次请求/小时"
echo "   - 高质量图片"
echo ""
echo "2. 使用免费图片网站（无需API Key）"
echo "   - 使用Unsplash、Pixabay等网站"
echo "   - 直接下载图片"
echo "   - 无需注册"
echo ""
echo "3. 使用自己的图片"
echo "   - 提供图片URL或本地路径"
echo "   - 完全自定义"
echo ""
echo "4. 跳过图片配置"
echo "   - 仅发布文字内容"
echo "   - 以后再配置图片"
echo ""

read -p "请选择方案 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "=========================================="
        echo "设置Pexels API Key"
        echo "=========================================="
        echo ""
        echo "请按以下步骤操作："
        echo ""
        echo "1. 访问 https://www.pexels.com/api/"
        echo "2. 点击 'Get Started' 注册账号"
        echo "3. 填写基本信息（姓名、邮箱、用途说明）"
        echo "4. 获取API Key"
        echo ""

        # 打开浏览器
        echo "正在打开Pexels API注册页面..."
        open "https://www.pexels.com/api/"

        echo ""
        read -p "请输入您的Pexels API Key: " api_key

        if [ -n "$api_key" ]; then
            # 检查是否已存在于.zshrc
            if grep -q "PEXELS_API_KEY" ~/.zshrc; then
                echo "更新现有的PEXELS_API_KEY配置..."
                sed -i '' "s/export PEXELS_API_KEY=.*/export PEXELS_API_KEY=\"$api_key\"/" ~/.zshrc
            else
                echo "添加PEXELS_API_KEY到环境变量..."
                echo "export PEXELS_API_KEY=\"$api_key\"" >> ~/.zshrc
            fi

            # 立即生效
            export PEXELS_API_KEY="$api_key"

            echo ""
            echo "✓ Pexels API Key 已设置并生效"
            echo "  Key: ${api_key:0:10}..."

            # 测试配置
            echo ""
            echo "测试配置..."
            python3 /Users/piaoxian/x-post-project/scripts/fetch-image.py "technology" "/tmp/test-image.jpg" "$api_key" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo "✓ 配置测试成功"
                rm -f /tmp/test-image.jpg
            else
                echo "⚠ 配置测试失败，请检查API Key是否正确"
            fi
        else
            echo "✗ 未输入API Key"
        fi
        ;;

    2)
        echo ""
        echo "=========================================="
        echo "使用免费图片网站"
        echo "=========================================="
        echo ""
        echo "可用的免费图片网站："
        echo ""
        echo "1. Unsplash (https://unsplash.com)"
        echo "   - 高质量摄影图片"
        echo "   - 免费商用"
        echo ""
        echo "2. Pixabay (https://pixabay.com)"
        echo "   - 照片、矢量图、插画"
        echo "   - 免费商用"
        echo ""
        echo "3. Pexels (https://pexels.com)"
        echo "   - 照片和视频"
        echo "   - 免费商用"
        echo ""

        # 创建替代方案配置文件
        cat > /Users/piaoxian/x-post-project/config/image-sources.json << 'EOF'
{
  "alternative_sources": [
    {
      "name": "Unsplash",
      "url": "https://unsplash.com",
      "search_url": "https://unsplash.com/s/photos/",
      "download_pattern": "https://unsplash.com/photos/{id}/download",
      "free": true,
      "commercial_use": true
    },
    {
      "name": "Pixabay",
      "url": "https://pixabay.com",
      "search_url": "https://pixabay.com/images/search/",
      "download_pattern": "https://pixabay.com/api/",
      "free": true,
      "commercial_use": true
    },
    {
      "name": "Pexels",
      "url": "https://pexels.com",
      "search_url": "https://pexels.com/search/",
      "download_pattern": "https://www.pexels.com/photo/",
      "free": true,
      "commercial_use": true
    }
  ]
}
EOF

        echo "✓ 替代方案配置已保存到: /Users/piaoxian/x-post-project/config/image-sources.json"
        echo ""
        echo "使用方法："
        echo "1. 访问上述网站搜索图片"
        echo "2. 复制图片URL"
        echo "3. 在工作流中选择 '使用自己的图片' 选项"
        echo "4. 粘贴图片URL"
        ;;

    3)
        echo ""
        echo "=========================================="
        echo "使用自己的图片"
        echo "=========================================="
        echo ""
        echo "您可以："
        echo ""
        echo "1. 提供图片URL"
        echo "   - 从任何网站获取图片URL"
        echo "   - 工作流会自动下载"
        echo ""
        echo "2. 提供本地图片路径"
        echo "   - 使用本地已有的图片"
        echo "   - 直接复制到项目目录"
        echo ""

        # 创建配置文件
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

        echo "✓ 自定义图片配置已保存到: /Users/piaoxian/x-post-project/config/custom-images.json"
        echo ""
        echo "使用方法："
        echo "1. 准备好图片URL或本地路径"
        echo "2. 在工作流中选择 '使用自己的图片' 选项"
        echo "3. 输入图片URL或路径"
        ;;

    4)
        echo ""
        echo "=========================================="
        echo "跳过图片配置"
        echo "=========================================="
        echo ""
        echo "已跳过图片配置。"
        echo ""
        echo "工作流将："
        echo "1. 仅发布文字内容"
        echo "2. 不包含配图"
        echo "3. 以后可以随时配置图片"
        echo ""

        # 创建配置文件
        cat > /Users/piaoxian/x-post-project/config/skip-images.json << 'EOF'
{
  "skip_images": {
    "enabled": true,
    "reason": "用户选择跳过图片配置",
    "can_configure_later": true
  }
}
EOF

        echo "✓ 跳过图片配置已保存到: /Users/piaoxian/x-post-project/config/skip-images.json"
        ;;

    *)
        echo "无效选择"
        exit 1
        ;;
esac

# 显示下一步
echo ""
echo "=========================================="
echo "配置完成"
echo "=========================================="
echo ""
echo "下一步："
echo ""
echo "1. 运行测试验证配置："
echo "   /Users/piaoxian/x-post-project/scripts/test-workflow.sh"
echo ""
echo "2. 启动工作流："
echo "   /zcf:x-post-workflow"
echo ""
echo "3. 查看配置指南："
echo "   /Users/piaoxian/x-post-project/CONFIG-GUIDE.md"
echo ""

# 验证X认证
echo ""
echo "验证X平台认证..."
if bird check > /dev/null 2>&1; then
    echo "✓ X平台认证正常"
else
    echo "⚠ X平台认证未配置"
    echo "  运行 'bird login' 进行配置"
fi

echo ""
echo "配置设置完成！"
