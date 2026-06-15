# X Post Scheduler

X（Twitter）帖文定时发布工具。支持文字+图片帖文，自动设置定时时间，最后由用户手动点击Schedule确认。

## 功能

- 从文件或备忘录读取帖文内容
- 自动打开X发帖页面
- 粘贴文字和图片
- 自动点击Schedule post按钮
- 自动设置定时日期时间
- 自动点击Confirm确认时间
- **用户手动点击Schedule按钮完成发布**

## 使用方法

### 方式1：从文件发布

```bash
# 帖文内容文件格式（纯文字，无标题括号）
/path/to/post-content.txt

# 图片路径
/path/to/image.jpg
```

### 方式2：从备忘录发布

```bash
# 备忘录名称
"X帖文1-xxx"
```

## 执行流程

### Step 1: 准备内容

1. 读取帖文文字内容（纯文字，无标题/括号/说明）
2. 确认图片路径
3. 将文字复制到剪贴板

### Step 2: 打开X发帖页面

```bash
osascript -e '
tell application "Google Chrome"
    activate
    execute active tab of front window javascript "window.location.href = \"https://x.com/compose/post\""
end tell
'
```

等待5秒页面加载。

### Step 3: 粘贴文字

```bash
# 先点击编辑器
osascript -e '
tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
        const editor = document.querySelector(\"div[role=\\\"textbox\\\"]\") || document.querySelectorAll(\"div[contenteditable=true]\")[0];
        if (editor) { editor.focus(); editor.click(); }
    "
end tell
'

# 粘贴文字（文字已复制到剪贴板）
osascript -e '
tell application "System Events"
    keystroke "v" using command down
end tell
'
```

### Step 4: 粘贴图片

```bash
# 复制图片到剪贴板
osascript -e 'tell application "Finder" to set theFile to (POSIX file "/path/to/image.jpg") as alias' -e 'set the clipboard to (read theFile as JPEG picture)'

# 点击编辑器并粘贴
osascript -e '
tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
        const editor = document.querySelector(\"div[role=\\\"textbox\\\"]\") || document.querySelectorAll(\"div[contenteditable=true]\")[0];
        if (editor) { editor.focus(); editor.click(); }
    "
end tell
' && osascript -e '
tell application "System Events"
    keystroke "v" using command down
end tell
'
```

等待3秒图片上传。

### Step 5: 点击Schedule post按钮

```bash
osascript -e '
tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
        const buttons = document.querySelectorAll(\"button\");
        for (let btn of buttons) {
            const text = btn.innerText || btn.getAttribute(\"aria-label\") || \"\";
            if (text.includes(\"Schedule post\")) {
                btn.click();
                break;
            }
        }
    "
end tell
'
```

### Step 6: 设置定时日期时间

使用脚本时通过参数传入日期时间，格式为 `YYYY-MM-DD HH:MM`。

**时间格式转换：**
| 用户输入 | 脚本参数 | Month值 | Hour值 |
|---------|---------|---------|--------|
| 今晚9点 | `2026-05-25 21:00` | 5 | 21 |
| 明天上午10点 | `2026-05-26 10:00` | 5 | 10 |
| 下周一晚8点 | `2026-06-01 20:00` | 6 | 20 |

**月份映射：**
January=1, February=2, March=3, April=4, May=5, June=6, July=7, August=8, September=9, October=10, November=11, December=12

**小时映射（24小时制）：**
上午12点=0, 上午1点=1, ..., 上午11点=11, 下午12点=12, 下午1点=13, ..., 晚上9点=21, 晚上10点=22, 晚上11点=23

```bash
# 脚本示例：设置 2026-05-25 21:00
osascript -e '
tell application "Google Chrome"
    activate
    execute active tab of front window javascript "
        const selects = document.querySelectorAll(\"select\");
        selects[0].value = \"5\";   // May
        selects[0].dispatchEvent(new Event(\"change\", {bubbles: true}));
        selects[1].value = \"25\";  // Day
        selects[1].dispatchEvent(new Event(\"change\", {bubbles: true}));
        selects[2].value = \"2026\"; // Year
        selects[2].dispatchEvent(new Event(\"change\", {bubbles: true}));
        selects[3].value = \"21\";  // 9 PM
        selects[3].dispatchEvent(new Event(\"change\", {bubbles: true}));
        selects[4].value = \"0\";   // Minute
        selects[4].dispatchEvent(new Event(\"change\", {bubbles: true}));
        \"Done\"
    "
end tell
'
```

### Step 7: 点击Confirm确认时间

```bash
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
```

### Step 8: 验证并等待用户手动确认

验证页面显示正确的定时时间：

```bash
osascript -e '
tell application "Google Chrome"
    activate
    set pageText to execute active tab of front window javascript "document.body.innerText.substring(0, 500)"
    return pageText
end tell
'
```

确认显示 "Will send on [日期] at [时间]" 后：

**告知用户：**
> 定时已设置：[日期] [时间]
> 请手动点击Schedule按钮完成发布

**Linux用户**：使用 `scripts/post-with-schedule.py`（基于Playwright）代替AppleScript。

### Linux/macOS选择指南

| 操作系统 | 推荐脚本 |
|---------|---------|
| macOS | `scripts/post-with-schedule-v2.sh`（AppleScript）|
| Linux | `scripts/post-with-schedule.py`（Playwright）|

**等待用户确认后再进行下一步操作。**

## 注意事项

1. **文字必须纯文字** - 不能包含标题、括号、说明等无关内容
2. **使用剪贴板粘贴** - 避免手动输入导致乱码
3. **等待页面加载** - 每次导航后等待3-5秒
4. **截图验证** - 关键步骤截图确认
5. **用户手动确认Schedule** - 最后一步由用户操作

## 常见问题

### Q: Chrome显示城市背景而不是X页面
A: 新标签页扩展覆盖了页面。使用JavaScript获取实际页面内容：
```bash
osascript -e '
tell application "Google Chrome"
    activate
    set pageText to execute active tab of front window javascript "document.body.innerText.substring(0, 300)"
    return pageText
end tell
'
```

### Q: 时间选择器设置无效
A: React合成事件可能未触发。让用户手动调整时间。

### Q: 图片上传失败
A: 确保图片已正确复制到剪贴板，并点击编辑器后粘贴。
