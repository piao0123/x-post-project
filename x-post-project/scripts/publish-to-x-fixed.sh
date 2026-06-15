#!/bin/bash
# X Post Scheduler - Fixed Version
# 使用方法: ./publish-to-x-fixed.sh <内容文件> <图片路径> --schedule "YYYY-MM-DD HH:MM"

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

# 显示使用方法
show_usage() {
    echo "Usage: $0 <content_file> <image_file> --schedule <datetime>"
    echo ""
    echo "Options:"
    echo " <content_file> 帖子内容文件路径"
    echo " <image_file> 图片文件路径"
    echo " --schedule 定时发布时间（格式：YYYY-MM-DD HH:MM）"
    echo ""
    echo "Examples:"
    echo " $0 post.md image.jpg --schedule '2026-06-15 21:00'"
}

# 参数解析
parse_arguments() {
    POST_FILE=""
    IMAGE_PATH=""
    SCHEDULE_DATETIME=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --schedule)
                SCHEDULE_DATETIME="$2"
                shift 2
                ;;
            *)
                if [ -z "$POST_FILE" ]; then
                    POST_FILE="$1"
                elif [ -z "$IMAGE_PATH" ]; then
                    IMAGE_PATH="$1"
                fi
                shift
                ;;
        esac
    done

    # 验证必要参数
    if [ -z "$POST_FILE" ]; then
        print_error "缺少必要参数：内容文件路径"
        show_usage
        exit 1
    fi

    if [ ! -f "$POST_FILE" ]; then
        print_error "内容文件不存在: $POST_FILE"
        exit 1
    fi

    if [ -z "$IMAGE_PATH" ]; then
        print_error "缺少图片文件路径"
        show_usage
        exit 1
    fi

    if [ ! -f "$IMAGE_PATH" ]; then
        print_error "图片文件不存在: $IMAGE_PATH"
        exit 1
    fi

    if [ -z "$SCHEDULE_DATETIME" ]; then
        print_error "缺少定时发布时间"
        show_usage
        exit 1
    fi

    # 解析定时时间
    YEAR=$(echo "$SCHEDULE_DATETIME" | cut -d'-' -f1)
    MONTH=$(echo "$SCHEDULE_DATETIME" | cut -d'-' -f2 | sed 's/^0//')
    DAY=$(echo "$SCHEDULE_DATETIME" | cut -d'-' -f3 | cut -d' ' -f1 | sed 's/^0//')
    HOUR=$(echo "$SCHEDULE_DATETIME" | cut -d' ' -f2 | cut -d':' -f1 | sed 's/^0//')
    MINUTE=$(echo "$SCHEDULE_DATETIME" | cut -d' ' -f2 | cut -d':' -f2 | sed 's/^0//')
}

# 检查Chrome是否运行
check_chrome_running() {
    if ! pgrep -x "Google Chrome" > /dev/null; then
        print_warn "Google Chrome未运行，正在启动..."
        open -a "Google Chrome"
        sleep 3
    fi
}

# 等待页面加载
wait_for_page_load() {
    local max_wait=30
    local wait_count=0

    print_info "等待页面加载..."
    while [ $wait_count -lt $max_wait ]; do
        local page_ready=$(osascript -e '
        tell application "Google Chrome"
        try
            set pageReady to execute active tab of front window javascript "
            document.readyState === \"complete\" && document.querySelector(\"div[role=\"textbox\"]\") !== null
            "
            return pageReady
        on error
            return false
        end try
        end tell
        ' 2>/dev/null || echo "false")

        if [ "$page_ready" = "true" ]; then
            print_info "页面加载完成"
            return 0
        fi

        sleep 1
        wait_count=$((wait_count + 1))
    done

    print_warn "页面加载超时，继续执行..."
    return 1
}

# 提取最终帖子内容（去除所有元数据和路径信息）
extract_final_content() {
    local content_file="$1"
    local output_file="$2"

    print_info "提取最终帖子内容..."

    # 读取文件，只保留纯文本内容（去除标题、标签、路径等）
    # 只保留第一行非空行，且去除任何Markdown格式
    grep -v "^#" "$content_file" | grep -v "^$" | head -1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' > "$output_file"

    # 验证内容
    local final_content=$(cat "$output_file")
    local char_count=${#final_content}

    if [ $char_count -eq 0 ]; then
        print_error "提取的内容为空"
        exit 1
    fi

    print_info "提取的内容: \"$final_content\""
    print_info "字符数: $char_count"

    if [ $char_count -gt 280 ]; then
        print_error "内容超出280字符限制: $char_count 字符"
        exit 1
    fi

    print_info "✓ 内容提取成功"
}

# 打开X发帖页面
open_compose_page() {
    print_info "[1/7] 打开发帖页面..."

    osascript -e '
    tell application "Google Chrome"
    activate
    execute active tab of front window javascript "window.location.href = \"https://x.com/compose/post\""
    end tell
    '

    # 等待页面加载
    wait_for_page_load
    sleep 2

    return 0
}

# 粘贴文字内容
paste_text() {
    local content_file="$1"

    print_info "[2/7] 粘贴文字内容..."

    # 复制内容到剪贴板
    cat "$content_file" | pbcopy

    # 点击编辑器获取焦点
    osascript -e '
    tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
    const editor = document.querySelector(\"div[role=\"textbox\"]\") ||
    document.querySelector(\"div[data-testid=\"tweetTextarea_0\"]\") ||
    document.querySelector(\"div[contenteditable=true]\");
    if (editor) {
        editor.focus();
        editor.click();
    }
    "
    end tell
    '
    sleep 0.5

    # 粘贴文字
    osascript -e '
    tell application "System Events"
    keystroke "v" using command down
    end tell
    '
    sleep 1

    # 验证粘贴是否成功
    local text_in_editor=$(osascript -e '
    tell application "Google Chrome"
    try
        set textInEditor to execute active tab of front window javascript "
        const editor = document.querySelector(\"div[role=\"textbox\"]\") ||
        document.querySelector(\"div[data-testid=\"tweetTextarea_0\"]\") ||
        document.querySelector(\"div[contenteditable=true]\");
        if (editor) { editor.innerText || editor.textContent || \"\" }
        "
        return textInEditor
    on error
        return \"\"
    end try
    end tell
    ' 2>/dev/null || echo "")

    if [ -n "$text_in_editor" ]; then
        print_info "文字粘贴成功"
        return 0
    else
        print_warn "文字粘贴可能失败"
        return 1
    fi
}

# 点击Media图标
click_media_button() {
    print_info "[3/7] 点击Media图标..."

    # 等待Media按钮出现
    osascript -e '
    tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
    const mediaButton = Array.from(document.querySelectorAll(\"button\")).find(btn =>
        btn.innerText.includes(\"Media\") || btn.getAttribute(\"aria-label\")?.includes(\"Media\")
    );
    if (mediaButton) {
        mediaButton.click();
        true;
    } else {
        false;
    }
    "
    end tell
    '
    sleep 2

    # 验证是否成功点击
    local media_clicked=$(osascript -e '
    tell application "Google Chrome"
    try
        set mediaClicked to execute active tab of front window javascript "
        const mediaButton = Array.from(document.querySelectorAll(\"button\")).find(btn =>
            btn.innerText.includes(\"Media\") || btn.getAttribute(\"aria-label\")?.includes(\"Media\")
        );
        mediaButton && mediaButton.parentElement && mediaButton.parentElement.querySelector(\"input[type=\"file\"]\") !== null;
        "
        return mediaClicked
    on error
        return false
    end try
    end tell
    ' 2>/dev/null || echo "false")

    if [ "$media_clicked" = "true" ]; then
        print_info "Media图标点击成功"
        return 0
    else
        print_warn "Media图标点击可能失败"
        return 1
    fi
}

# 设置定时发布
set_schedule_datetime() {
    print_info "[4/7] 设置定时: $YEAR-$MONTH-$DAY $HOUR:$MINUTE..."

    # 等待Schedule按钮出现
    osascript -e '
    tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
    const scheduleButton = Array.from(document.querySelectorAll(\"button\")).find(btn =>
        btn.innerText.includes(\"Schedule\") || btn.innerText.includes(\"Schedule post\")
    );
    if (scheduleButton) {
        scheduleButton.click();
        true;
    } else {
        false;
    }
    "
    end tell
    '
    sleep 2

    # 设置日期时间
    osascript -e "
    tell application \"Google Chrome\"
    activate
    execute active tab of front window javascript \"
    // 等待日期选择器出现
    const waitForSelects = () => {
        return new Promise((resolve) => {
            const check = () => {
                const selects = document.querySelectorAll('select');
                if (selects.length >= 5) {
                    resolve(selects);
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    };

    waitForSelects().then(selects => {
        // 设置月份
        selects[0].value = \"$MONTH\";
        selects[0].dispatchEvent(new Event('change', {bubbles: true}));

        // 设置日期
        selects[1].value = \"$DAY\";
        selects[1].dispatchEvent(new Event('change', {bubbles: true}));

        // 设置年份
        selects[2].value = \"$YEAR\";
        selects[2].dispatchEvent(new Event('change', {bubbles: true}));

        // 设置小时
        selects[3].value = \"$HOUR\";
        selects[3].dispatchEvent(new Event('change', {bubbles: true}));

        // 设置分钟
        selects[4].value = \"$MINUTE\";
        selects[4].dispatchEvent(new Event('change', {bubbles: true}));
    });
    \"Done\"
    "
    end tell
    "
    sleep 1

    # 点击Confirm确认时间
    print_info "点击Confirm确认时间..."
    osascript -e '
    tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
    const buttons = document.querySelectorAll(\"button\");
    for (let btn of buttons) {
        if (btn.innerText && btn.innerText.includes(\"Confirm\")) {
            btn.click();
            break;
        }
    }
    "
    end tell
    '
    sleep 2

    return 0
}

# 主函数
main() {
    print_info "=== X Post Scheduler - Fixed Version ==="
    echo ""

    # 解析参数
    parse_arguments "$@"

    # 显示配置信息
    print_info "发布配置:"
    print_info " 内容文件: $POST_FILE"
    print_info " 图片文件: $IMAGE_PATH"
    print_info " 定时时间: $YEAR-$MONTH-$DAY $HOUR:$MINUTE"
    echo ""

    # 检查Chrome是否运行
    check_chrome_running

    # 创建临时文件存储提取的内容
    TEMP_CONTENT=$(mktemp)

    # 提取最终帖子内容
    extract_final_content "$POST_FILE" "$TEMP_CONTENT"

    # 执行发布流程
    open_compose_page
    paste_text "$TEMP_CONTENT"
    click_media_button
    set_schedule_datetime

    # 清理临时文件
    rm -f "$TEMP_CONTENT"

    echo ""
    print_info "=== 完成 ==="
    print_info "X发帖页面已打开，内容已填充，Media图标已点击，定时已设置。"
    print_info "请手动选择图片文件，然后点击'Schedule'按钮完成发布。"
}

# 运行主函数
main "$@"