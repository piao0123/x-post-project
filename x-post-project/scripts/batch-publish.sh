#!/bin/bash
# 批量发布脚本 - 为所有分区的帖子设置定时发布

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
SCHEDULE_SCRIPT="/Users/piaoxian/.claude/skills/x-post-scheduler/scripts/post-with-schedule-v2.sh"
BASE_DIR="/Users/piaoxian/x-post-project/posts"
START_HOUR=21
START_MINUTE=0
INTERVAL_MINUTES=15 # 每15分钟发布一篇

# 分区列表
CATEGORIES=("tech" "entertainment" "lifestyle" "gaming" "music")

# 默认参数
DRY_RUN=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 发布单个帖子
publish_post() {
    local category=$1
    local post_num=$2
    local schedule_time=$3

    local content_file="$BASE_DIR/$category/0${post_num}-post-final.md"
    local image_file="$BASE_DIR/$category/images/0${post_num}-image.jpg"

    if [ ! -f "$content_file" ]; then
        print_error "内容文件不存在: $content_file"
        return 1
    fi

    print_info "发布帖子: $category/$post_num"
    print_info "内容文件: $content_file"
    print_info "图片文件: $image_file"
    print_info "发布时间: $schedule_time"

    if [ "$DRY_RUN" = true ]; then
        print_info "[DRY-RUN] 跳过发布: $content_file @ $schedule_time"
        return 0
    fi

    # 执行发布脚本
    if [ -f "$image_file" ]; then
        "$SCHEDULE_SCRIPT" "$content_file" "$image_file" --schedule "$schedule_time"
    else
        "$SCHEDULE_SCRIPT" "$content_file" --schedule "$schedule_time"
    fi
}

# 计算发布时间
calculate_schedule_time() {
    local index=$1
    local total_minutes=$((START_HOUR * 60 + START_MINUTE + index * INTERVAL_MINUTES))
    local hour=$((total_minutes / 60))
    local minute=$((total_minutes % 60))
    local date_str=$(date "+%Y-%m-%d")

    printf "%s %02d:%02d" "$date_str" "$hour" "$minute"
}

# 主函数
main() {
    print_info "开始批量发布..."
    print_info "总帖子数: 15"
    print_info "发布间隔: $INTERVAL_MINUTES 分钟"
    print_info "开始时间: $START_HOUR:$START_MINUTE"
    echo ""

    local index=0
    local success_count=0
    local fail_count=0

    for category in "${CATEGORIES[@]}"; do
        print_info "处理分区: $category"

        for post_num in 1 2 3; do
            local schedule_time=$(calculate_schedule_time $index)

            if publish_post "$category" "$post_num" "$schedule_time"; then
                ((success_count++))
                print_info "✅ 帖子 $category/$post_num 发布成功"
            else
                ((fail_count++))
                print_error "❌ 帖子 $category/$post_num 发布失败"
            fi

            ((index++))
            echo ""
        done
    done

    echo ""
    print_info "批量发布完成"
    print_info "成功: $success_count"
    print_info "失败: $fail_count"
}

# 执行主函数
main "$@"