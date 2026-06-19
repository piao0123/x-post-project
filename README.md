# X Post Project

X（Twitter）帖子创作发布自动化工具，支持 macOS 和 Linux。

## 🖥️ 平台支持

| 操作系统 | 发布脚本 | 依赖 |
|---------|---------|------|
| macOS | `scripts/post-with-schedule-v2.sh` | AppleScript + Chrome |
| Linux | `scripts/post-with-schedule.py` | Playwright + Chromium |

## 📁 目录结构

```
x-post-project/
├── SKILL.md                          # 主skill说明文档
├── README.md                          # 本文件
├── scripts/
│   ├── post-with-schedule.py          # Linux发布脚本（Playwright）
│   ├── post-with-schedule-v2.sh       # macOS发布脚本（AppleScript）
│   ├── check-char-count.py            # X字数检查工具
│   └── post-with-schedule.sh          # macOS脚本v1（旧版）
├── x-post-workflow/
│   └── SKILL.md                       # 完整工作流skill
├── x-post-scheduler/
│   ├── SKILL.md                       # 定时发布skill
│   └── scripts/                       # 软链接到上方scripts/
│       ├── post-with-schedule.sh -> ../../scripts/post-with-schedule.sh
│       └── post-with-schedule-v2.sh -> ../../scripts/post-with-schedule-v2.sh
└── posts/                             # 帖子内容存放目录
```

## 🚀 快速开始

### Step 1: 安装依赖（Linux）

```bash
pip3 install playwright
playwright install chromium
apt install chromium-browser
```

### Step 2: 内容抓取

使用 Exa 搜索抓取热门帖子（推荐）：

```bash
# 需要配置 mcporter / Exa API
mcporter call 'exa.web_search_exa(query: "site:twitter.com 关键词 min_faves:1000", numResults: 5)'
```

可选：如果已经在 OpenClaw 中安装 [TweetClaw](https://docs.xquik.com)，可以先准备一个经过人工审核的 X/Twitter 来源包，再进入仿写和发布流程。

- 只保留公开帖子 URL、作者、正文摘要、发布时间、媒体提示和查询词。
- 保存为 `posts/{category}/source-packet.json`，再由本项目完成选题、仿写、字数检查和发布。
- 不要写入 API key、cookie、私信、未审核草稿、自动发布授权或账号操作指令。
- TweetClaw 只负责来源采集；最终内容、发布时间和发布动作仍由用户确认。

### Step 3: 字数检查

```bash
# 直接检查文本
python3 scripts/check-char-count.py "这是测试内容"

# 检查文件（自动去除markdown格式）
python3 scripts/check-char-count.py posts/category/02-post-humanized.md
```

### Step 4: 发布帖子

**Linux（推荐）：**
```bash
# 立即发布
python3 scripts/post-with-schedule.py content.txt

# 定时发布
python3 scripts/post-with-schedule.py content.txt --schedule "2026-06-15 21:00"

# 带图片 + 定时
python3 scripts/post-with-schedule.py content.txt image.jpg --schedule "2026-06-15 21:00"
```

**macOS：**
```bash
# 立即发布
bash scripts/post-with-schedule-v2.sh content.txt

# 定时发布
bash scripts/post-with-schedule-v2.sh content.txt image.jpg --schedule "2026-06-15 21:00"
```

## 🔧 主要修复记录

### 2026-06-15
- 新增 Linux 版发布脚本 `post-with-schedule.py`（基于 Playwright）
- 修复日期时间前导零 Bug（`sed 's/^0//'` 导致 X select value 不匹配）
- 新增 `check-char-count.py` 字数检查脚本
- 移除所有硬编码 `/Users/piaoxian/` 路径
- 清理重复脚本，使用软链接统一管理
- 支持读取 .md 文件并自动提取纯文本

## ⚠️ 已知限制

- **Twitter API 免费套餐**：不支持搜索，只能发推文
- **Linux 剪贴板**：需要 `xclip`（可选，脚本改用键盘直接输入）
- **X 页面结构变化**：X 页面更新后可能需要调整选择器
