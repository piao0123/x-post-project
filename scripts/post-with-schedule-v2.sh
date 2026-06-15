#!/bin/bash
# X Post Scheduler v2 - 优化版
# 使用方法: ./post-with-schedule-v2.sh <文字文件> [图片路径] [--schedule <日期时间>]
#
# 示例:
#   ./post-with-schedule-v2.sh /tmp/post.txt
#   ./post-with-schedule-v2.sh /tmp/post.txt /path/to/image.jpg
#   ./post-with-schedule-v2.sh /tmp/post.txt /path/to/image.jpg --schedule "2026-05-26 21:00"

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
            --help|-h)
                show_usage
                exit 0
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

    # 验证图片文件
    if [ -n "$IMAGE_PATH" ] && [ ! -f "$IMAGE_PATH" ]; then
        print_error "图片文件不存在: $IMAGE_PATH"
        exit 1
    fi

    # 解析日期时间（不移除前导零！X的select value可能是 "05"）
    if [ -n "$SCHEDULE_DATETIME" ]; then
        YEAR=$(echo "$SCHEDULE_DATETIME" | cut -d'-' -f1)
        MONTH=$(echo "$SCHEDULE_DATETIME" | cut -d'-' -f2)           # 保持 "05"
        DAY=$(echo "$SCHEDULE_DATETIME" | cut -d'-' -f3 | cut -d' ' -f1)   # 保持 "27"
        HOUR=$(echo "$SCHEDULE_DATETIME" | cut -d' ' -f2 | cut -d':' -f1)   # 保持 "09"
        MINUTE=$(echo "$SCHEDULE_DATETIME" | cut -d' ' -f2 | cut -d':' -f2) # 保持 "00"
    fi
}

# ── Bug修复说明 ─────────────────────────────────────
# 原版使用 sed 's/^0//' 移除前导零，导致:
#   输入 "2026-05-09 09:00" → MONTH=5, HOUR=9
#   但X的select value是 "05"、"09"，导致设置失败
# 本版本保持前导零，解决此问题



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
                    document.readyState === \"complete\" && document.querySelector(\"div[role=\\\"textbox\\\"]\") !== null
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

# 检查Chrome是否运行
check_chrome_running() {
    if ! pgrep -x "Google Chrome" > /dev/null; then
        print_warn "Google Chrome未运行，正在启动..."
        open -a "Google Chrome"
        sleep 3
    fi
}

# Step 1: 复制文字到剪贴板
copy_text_to_clipboard() {
    print_info "[1/7] 复制文字到剪贴板..."
    cat "$POST_FILE" | pbcopy

    # 验证剪贴板内容
    local clipboard_content=$(pbpaste)
    if [ -z "$clipboard_content" ]; then
        print_error "剪贴板内容为空"
        return 1
    fi

    print_info "文字已复制到剪贴板"
    return 0
}

# Step 2: 打开X发帖页面
open_compose_page() {
    print_info "[2/7] 打开发帖页面..."

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

# Step 3: 粘贴文字
paste_text() {
    print_info "[3/7] 粘贴文字..."

    # 先点击编辑器获取焦点
    local editor_found=$(osascript -e '
    tell application "Google Chrome"
        activate
        set editorFound to execute active tab of front window javascript "
            const editor = document.querySelector(\"div[role=\\\"textbox\\\"]\") ||
                           document.querySelector(\"div[data-testid=\\\"tweetTextarea_0\\\"]\") ||
                           document.querySelector(\"div[contenteditable=true]\");
            if (editor) {
                editor.focus();
                editor.click();
                true;
            } else {
                false;
            }
        "
        return editorFound
    end tell
    ' 2>/dev/null || echo "false")

    sleep 0.5

    # 粘贴文字
    osascript -e '
    tell application "System Events"
        keystroke "v" using command down
    end tell
    '
    sleep 1

    # 如果编辑器找到，认为粘贴成功
    if [ "$editor_found" = "true" ]; then
        print_info "文字粘贴成功"
        return 0
    else
        print_warn "未找到编辑器，文字粘贴可能失败"
        return 1
    fi
}

# Step 4: 复制图片到剪贴板
copy_image_to_clipboard() {
    if [ -z "$IMAGE_PATH" ]; then
        print_info "[4/7] 无图片，跳过..."
        return 0
    fi

    print_info "[4/7] 复制图片到剪贴板..."

    # 检查图片文件是否存在
    if [ ! -f "$IMAGE_PATH" ]; then
        print_error "图片文件不存在: $IMAGE_PATH"
        return 1
    fi

    # 获取文件扩展名
    local ext="${IMAGE_PATH##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    # 根据文件类型选择复制方式
    case "$ext" in
        jpg|jpeg)
            osascript -e "
            tell application \"Finder\"
                set theFile to (POSIX file \"$IMAGE_PATH\") as alias
            end tell
            tell application \"System Events\"
                set the clipboard to (read theFile as JPEG picture)
            end tell
            "
            ;;
        png)
            osascript -e "
            tell application \"Finder\"
                set theFile to (POSIX file \"$IMAGE_PATH\") as alias
            end tell
            tell application \"System Events\"
                set the clipboard to (read theFile as PNG picture)
            end tell
            "
            ;;
        gif)
            osascript -e "
            tell application \"Finder\"
                set theFile to (POSIX file \"$IMAGE_PATH\") as alias
            end tell
            tell application \"System Events\"
                set the clipboard to (read theFile as GIF picture)
            end tell
            "
            ;;
        *)
            print_warn "不支持的图片格式: $ext"
            return 1
            ;;
    esac

    print_info "图片已复制到剪贴板"
    return 0
}

# Step 5: 粘贴图片
paste_image() {
    if [ -z "$IMAGE_PATH" ]; then
        print_info "[5/7] 无图片，跳过..."
        return 0
    fi

    print_info "[5/7] 粘贴图片..."

    # 先点击编辑器获取焦点
    osascript -e '
    tell application "Google Chrome"
        activate
        execute active tab of front window javascript "
            const editor = document.querySelector(\"div[role=\\\"textbox\\\"]\") ||
                           document.querySelector(\"div[data-testid=\\\"tweetTextarea_0\\\"]\") ||
                           document.querySelector(\"div[contenteditable=true]\");
            if (editor) {
                editor.focus();
                editor.click();
                true;
            } else {
                false;
            }
        "
    end tell
    '
    sleep 0.5

    # 粘贴图片
    osascript -e '
    tell application "System Events"
        keystroke "v" using command down
    end tell
    '
    sleep 3

    # 验证图片是否上传成功
    local image_uploaded=$(osascript -e '
    tell application "Google Chrome"
        try
            set hasImage to execute active tab of front window javascript "
                document.querySelector(\"img[alt=\\\"Image\\\"]\") !== null ||
                document.querySelector(\"div[data-testid=\\\"tweetPhoto\\\"]\") !== null
            "
            return hasImage
        on error
            return false
        end try
    end tell
    ' 2>/dev/null || echo "false")

    if [ "$image_uploaded" = "true" ]; then
        print_info "图片上传成功"
        return 0
    else
        print_warn "图片上传可能失败，请手动检查"
        return 1
    fi
}

# Step 6: 点击Schedule post按钮
click_schedule_button() {
    print_info "[6/7] 点击Schedule post..."

    osascript -e '
    tell application "Google Chrome"
        activate
        execute active tab of front window javascript "
            const buttons = document.querySelectorAll(\"button\");
            for (let btn of buttons) {
                const text = btn.innerText || btn.getAttribute(\"aria-label\") || \"\";
                if (text.includes(\"Schedule post\") || text.includes(\"Schedule\")) {
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

# Step 7: 设置日期时间
set_schedule_datetime() {
    if [ -z "$SCHEDULE_DATETIME" ]; then
        print_info "[7/7] 无定时时间，跳过..."
        return 0
    fi

    print_info "[7/7] 设置定时: $YEAR-$MONTH-$DAY $HOUR:$MINUTE..."

    # 使用更可靠的方式设置日期时间
    osascript -e "
    tell application \"Google Chrome\"
        activate
        execute active tab of front window javascript \"
            // 等待日期选择器出现
            const waitForSelects = () => {
                return new Promise((resolve) => {
                    const check = () => {
                        const selects = document.querySelectorAll(\"select\");
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
                selects[0].dispatchEvent(new Event(\"change\", {bubbles: true}));

                // 设置日期
                selects[1].value = \"$DAY\";
                selects[1].dispatchEvent(new Event(\"change\", {bubbles: true}));

                // 设置年份
                selects[2].value = \"$YEAR\";
                selects[2].dispatchEvent(new Event(\"change\", {bubbles: true}));

                // 设置小时
                selects[3].value = \"$HOUR\";
                selects[3].dispatchEvent(new Event(\"change\", {bubbles: true}));

                // 设置分钟
                selects[4].value = \"$MINUTE\";
                selects[4].dispatchEvent(new Event(\"change\", {bubbles: true}));
            });

            \"Done\"
        \"
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

# 验证设置
verify_settings() {
    print_info "验证设置..."

    osascript -e '
    tell application "Google Chrome"
        activate
        set pageText to execute active tab of front window javascript "document.body.innerText.substring(0, 500)"
        return pageText
    end tell
    '

    return 0
}

# 主函数
main() {
    print_info "=== X Post Scheduler v2 ==="
    echo ""

    # 解析参数
    parse_arguments "$@"

    # 显示配置信息
    print_info "发布配置:"
    print_info "  内容文件: $POST_FILE"
    print_info "  图片文件: ${IMAGE_PATH:-无}"
    print_info "  定时时间: ${SCHEDULE_DATETIME:-立即发布}"
    echo ""

    # 检查Chrome是否运行
    check_chrome_running

    # 执行发布流程
    copy_text_to_clipboard
    open_compose_page
    paste_text
    copy_image_to_clipboard
    paste_image
    click_schedule_button
    set_schedule_datetime

    # 验证设置
    echo ""
    verify_settings

    echo ""
    print_info "=== 完成 ==="
    if [ -n "$SCHEDULE_DATETIME" ]; then
        print_info "定时已设置: $YEAR-$MONTH-$DAY $HOUR:$MINUTE"
    fi
    print_info "请手动点击Schedule按钮完成发布。"
}

# 运行主函数
main "$@"
