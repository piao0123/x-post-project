#!/bin/bash

# X帖子发布脚本（优化版）
# 优先使用x-post-scheduler，bird tweet作为备选

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用方法
show_usage() {
    echo "Usage: $0 <content_file> [image_file] [--schedule <datetime>]"
    echo ""
    echo "Options:"
    echo "  <content_file>  帖子内容文件路径"
    echo "  [image_file]    图片文件路径（可选）"
    echo "  --schedule      定时发布时间（格式：YYYY-MM-DD HH:MM）"
    echo ""
    echo "Examples:"
    echo "  $0 post.md                          # 发布纯文字帖子"
    echo "  $0 post.md image.jpg                # 发布带图片的帖子"
    echo "  $0 post.md image.jpg --schedule '2026-05-26 21:00'  # 定时发布"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    # 检查x-post-scheduler
    if [ -f "/Users/piaoxian/.claude/skills/x-post-scheduler/scripts/post-with-schedule.sh" ]; then
        print_info "✓ x-post-scheduler 已安装"
    else
        print_warn "✗ x-post-scheduler 未安装"
    fi

    # 检查bird CLI
    if command -v bird &> /dev/null; then
        print_info "✓ bird CLI 已安装"
    else
        print_warn "✗ bird CLI 未安装"
    fi

    # 检查curl
    if command -v curl &> /dev/null; then
        print_info "✓ curl 已安装"
    else
        print_error "✗ curl 未安装"
        exit 1
    fi

    # 检查X认证
    if bird check &> /dev/null; then
        print_info "✓ X平台认证正常"
    else
        print_warn "✗ X平台认证未配置"
    fi
}

# 尝试使用x-post-scheduler发布
try_x_post_scheduler() {
    local content_file="$1"
    local image_file="$2"
    local schedule_time="$3"

    print_info "尝试使用x-post-scheduler发布..."

    # 优先使用v2版本，备选v1版本
    local scheduler_script="/Users/piaoxian/.claude/skills/x-post-scheduler/scripts/post-with-schedule-v2.sh"
    if [ ! -f "$scheduler_script" ]; then
        scheduler_script="/Users/piaoxian/.claude/skills/x-post-scheduler/scripts/post-with-schedule.sh"
    fi

    if [ ! -f "$scheduler_script" ]; then
        print_warn "x-post-scheduler脚本不存在"
        return 1
    fi

    # 构建命令
    local cmd="$scheduler_script \"$content_file\""
    if [ -n "$image_file" ] && [ -f "$image_file" ]; then
        cmd="$cmd \"$image_file\""
    fi
    if [ -n "$schedule_time" ]; then
        cmd="$cmd --schedule \"$schedule_time\""
    fi

    # 执行命令
    if eval $cmd; then
        print_info "✓ 使用x-post-scheduler发布成功"
        return 0
    else
        print_warn "✗ x-post-scheduler发布失败"
        return 1
    fi
}

# 尝试使用bird tweet发布
try_bird_publish() {
    local content_file="$1"
    local image_file="$2"
    local schedule_time="$3"

    print_info "尝试使用bird tweet发布（备选方案）..."

    # 读取内容
    local content=$(cat "$content_file")

    # 构建命令
    local cmd="bird tweet \"$content\""

    # 如果有图片，添加媒体参数
    if [ -n "$image_file" ] && [ -f "$image_file" ]; then
        cmd="$cmd --media $image_file"
    fi

    # 执行命令
    if eval $cmd; then
        print_info "✓ 使用bird tweet发布成功"
        return 0
    else
        print_warn "✗ bird tweet发布失败"
        return 1
    fi
}

# 生成手动发布指南
generate_manual_guide() {
    local content_file="$1"
    local image_file="$2"
    local schedule_time="$3"
    local output_file="$(dirname "$content_file")/MANUAL-PUBLISH-GUIDE.md"

    print_info "生成手动发布指南..."

    # 读取内容
    local content=$(cat "$content_file")

    # 生成指南
    cat > "$output_file" << EOF
# 手动发布指南

## 发布时间
$(date)

## 帖子内容

\`\`\`
$content
\`\`\`

## 图片
$([ -n "$image_file" ] && echo "图片路径: $image_file" || echo "无图片")

## 发布步骤

### 1. 打开X发帖页面
访问: https://x.com/compose/post

### 2. 复制文字内容
复制上面的文字内容，粘贴到发帖框

### 3. 上传图片（如有）
$([ -n "$image_file" ] && echo "点击图片按钮，上传: $image_file" || echo "跳过此步骤")

### 4. 设置定时发布（如有）
$([ -n "$schedule_time" ] && echo "设置时间: $schedule_time" || echo "立即发布")

### 5. 发布
点击"Post"或"Schedule"按钮完成发布

## 发布检查清单

- [ ] 文字内容已复制
- [ ] 图片已上传（如有）
- [ ] 定时时间已设置（如有）
- [ ] 内容已预览确认
- [ ] 点击发布按钮

## 常见问题

### Q: 如何设置定时发布？
A: 在发帖框下方找到"Schedule"按钮，选择"Schedule for later"，设置日期和时间。

### Q: 图片上传失败怎么办？
A: 检查图片格式（支持JPG、PNG、GIF、WebP），确保文件大小不超过5MB。

### Q: 发布后可以修改吗？
A: 发布后可以编辑或删除帖子。

## 发布确认

发布完成后，请确认以下信息：
1. 帖子已成功发布
2. 内容显示正确
3. 图片显示正常（如有）
4. 定时时间正确（如有）

如有问题，请检查X平台状态或联系支持。

---
生成时间: $(date)
EOF

    print_info "✓ 手动发布指南已生成: $output_file"
    echo "$output_file"
}

# 主函数
main() {
    # 检查参数
    if [ $# -lt 1 ]; then
        show_usage
        exit 1
    fi

    local content_file="$1"
    local image_file=""
    local schedule_time=""

    # 解析参数
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --schedule)
                schedule_time="$2"
                shift 2
                ;;
            *)
                image_file="$1"
                shift
                ;;
        esac
    done

    # 检查文件是否存在
    if [ ! -f "$content_file" ]; then
        print_error "内容文件不存在: $content_file"
        exit 1
    fi

    if [ -n "$image_file" ] && [ ! -f "$image_file" ]; then
        print_error "图片文件不存在: $image_file"
        exit 1
    fi

    # 显示信息
    print_info "发布配置:"
    print_info "  内容文件: $content_file"
    print_info "  图片文件: ${image_file:-无}"
    print_info "  定时时间: ${schedule_time:-立即发布}"

    # 检查依赖
    check_dependencies

    # 优先尝试x-post-scheduler发布
    echo ""
    print_info "优先尝试x-post-scheduler发布..."
    if try_x_post_scheduler "$content_file" "$image_file" "$schedule_time"; then
        print_info "✓ x-post-scheduler发布成功"
        exit 0
    fi

    # x-post-scheduler失败，尝试bird tweet
    echo ""
    print_warn "x-post-scheduler失败，尝试bird tweet..."
    if try_bird_publish "$content_file" "$image_file" "$schedule_time"; then
        print_info "✓ bird tweet发布成功"
        exit 0
    fi

    # 所有自动发布方式都失败，生成手动发布指南
    echo ""
    print_warn "所有自动发布方式都失败，生成手动发布指南..."
    guide_file=$(generate_manual_guide "$content_file" "$image_file" "$schedule_time")

    echo ""
    print_info "请按照以下步骤手动发布："
    print_info "1. 打开指南文件: $guide_file"
    print_info "2. 按照指南步骤操作"
    print_info "3. 完成发布后确认"

    # 尝试打开指南文件
    if command -v open &> /dev/null; then
        open "$guide_file"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$guide_file"
    fi
}

# 运行主函数
main "$@"
