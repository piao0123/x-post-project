---
name: x-post-workflow
description: >
  X帖子创作发布完整工作流。从X平台抓取热门内容、仿写创作、去除AI痕迹、搜索下载配图、定时发布。
  基于实际运行经验优化，解决了Twitter API限制、内容抓取、配图搜索、自动化发布等常见问题。
---

# X帖子创作发布工作流

端到端的X帖子创作和发布工作流，整合多个skill实现从内容抓取到定时发布的完整流程。

## 工作流概览

```
Step 1: 内容抓取 → Step 2: 用户选择 → Step 3: 仿写创作 → Step 4: 人性化处理
    ↓
Step 5: 配图搜索下载 → Step 6: 字数检查 → Step 7: 定时发布
```

## 8步工作流详解

---

### Step 1: 内容抓取 [自动]

**目的**: 从X平台抓取热门帖子内容

**工具优先级** (按可靠性排序):
1. **Exa搜索** (最可靠) - 搜索引用X帖子的新闻文章
2. **bird CLI** - 直接搜索X平台 (可能被反爬虫拦截)
3. **Twitter API** - 官方API (免费套餐不支持搜索)

**Exa搜索方法** (推荐):
```bash
# 搜索包含X帖子的新闻文章
mcporter call 'exa.web_search_exa(query: "site:twitter.com 关键词 min_faves:1000", numResults: 5)'
```

**Twitter API限制**:
- 免费套餐(Essentials): 只能发推文，不能搜索
- Basic套餐($100/月): 支持搜索功能
- 如需使用API搜索，需升级套餐

**bird CLI限制**:
- 可能被X平台反爬虫机制拦截
- 需要有效的登录cookie

**输出格式** (JSON):
```json
{
  "posts": [
    {
      "id": " tweet_id",
      "author": "@username",
      "content": "帖子内容",
      "date": "2026-05-27",
      "likes": 1000,
      "url": "https://x.com/username/status/tweet_id"
    }
  ]
}
```

**错误处理**:
- Exa搜索失败 → 尝试bird CLI
- bird CLI失败 → 提示用户检查X登录状态
- 所有方法失败 → 提示用户稍后重试

---

### Step 2: 用户选择 [交互点]

**目的**: 让用户选择要仿写的帖子

**交互方式**: AskUserQuestion，展示帖子列表供用户选择

**输出**: 保存选择到 `posts/{category}/selected-posts.json`

---

### Step 3: 仿写创作 [自动]

**目的**: 基于选中的帖子进行仿写创作

**仿写原则**:
1. **保持客观事实** - 事实部分与原文一致
2. **不使用个人经历口吻** - 避免"我"、"我的"等第一人称
3. **真正创作** - 不是简单总结，而是用新表达呈现相同内容
4. **保持风格** - 与原文风格一致（幽默/严肃/讽刺等）

**错误示例**:
```
原文: "This is the kind of Bollywood needed 😂"
错误仿写: "Bollywood's latest: Akshay Kumar teams with..." (像新闻标题)
正确仿写: "Akshay Kumar just dropped a Bhojpuri dance track and honestly? This is the chaotic energy Bollywood has been missing." (保持轻松风格)
```

**输出格式** (Markdown):
```markdown
# 帖子标题

## 原文
原始帖子内容

## 仿写
仿写后的内容

## 客观事实
- 事实1
- 事实2

## 配图路径
- /path/to/image.jpg
```

---

### Step 4: 人性化处理 [自动]

**目的**: 使用 `humanizer-skill` 去除AI写作痕迹

**调用方式**: 使用 Read tool 读取 `skills/humanizer-skill/SKILL.md`，按其指引调用 humanizer。

**humanizer 调用示例**:
```bash
# 检测AI痕迹（输出0-100评分）
humanizer "你的仿写内容" --mode detect --voice casual --score

# 人性化改写（推荐用于X帖子）
humanizer "你的仿写内容" --mode rewrite --voice casual --purpose social

# 原地编辑文件
humanizer --file posts/category/01-post-rewritten.md --mode edit --voice casual
```

**X帖子推荐humanizer参数**:
- `--voice casual` - 口语化、轻松，适合社交媒体
- `--purpose social` - 社交媒体优化
- `--score` - 先检测评分，>40分建议重写
- `--iterate 2` - 双重迭代确保质量

**关键规则（X帖子特别关注）**:
- P7: 移除AI高频词 (Additionally, crucial, delve, vibrant, pivotal等)
- P13: 禁止使用 Em Dash (——)，零容忍
- P10: 避免三段式列表
- P19: 移除 chatbot 话术 (Of course! Certainly! 等)
- P40: 移除意义解说句 ("代表了..." "象征着...")

**输出**: `posts/{category}/02-post-humanized.md`

**验证**: humanizer 输出 `[Score: NN/100]`，目标 <40 分

---

### Step 5: 配图搜索下载 [自动]

**目的**: 为帖子搜索并下载合适的配图

**图片API优先级** (按可用性排序):
1. **Unsplash** (免费，无需API Key) - 推荐
2. **Pexels** (免费，需API Key) - 备选
3. **本地已有图片** - 最可靠

**Unsplash搜索方法**:
```bash
# 搜索图片
curl -s "https://api.unsplash.com/search/photos?query=关键词&per_page=3" \
  -H "Authorization: Client-ID YOUR_KEY"

# 直接下载图片
curl -o "output.jpg" "https://images.unsplash.com/photo-ID?w=1200"
```

**图片要求**:
- 分辨率: 至少1200x800像素
- 格式: JPG或PNG
- 大小: 不超过5MB
- 内容: 与帖子主题相关

**错误处理**:
- API搜索失败 → 使用目录中已有的旧图片
- 下载失败 → 重试1次，失败后跳过配图
- 无合适图片 → 继续发布纯文字内容

**输出**: `posts/{category}/images/01-image.jpg`

---

### Step 6: 字数检查 [自动]

**目的**: 确保内容符合X平台字数限制

**限制规则**:
- 普通用户: 280字符
- Premium用户: 10,000字符
- URL计为23字符 (使用URL缩短)
- @用户名不计入字数

**检查脚本**:
```bash
python3 scripts/check-char-count.py "内容"
# 或读取文件:
python3 scripts/check-char-count.py posts/category/02-post-humanized.md
```

**处理逻辑**:
```python
if 字符数 > 280:
    if 用户是Premium:
        提示用户内容超过280字符，但仍在10000字符限制内
    else:
        自动精简内容到280字符以内
```

**输出**: `posts/{category}/03-post-final.md` (纯文字，无标题/说明)

---

### Step 7: 定时发布 [交互点 + 自动]

**目的**: 将内容和图片发布到X并设定定时

**发布脚本选择**:

| 操作系统 | 脚本 | 命令 |
|---------|------|------|
| Linux | `scripts/post-with-schedule.py` | `python3 scripts/post-with-schedule.py ...` |
| macOS | `scripts/post-with-schedule-v2.sh` | `bash scripts/post-with-schedule-v2.sh ...` |

**前置准备**:
1. 确保 `03-post-final.md` 为纯文字（无标题/说明/注释）
2. 确认图片路径（可选，无图片则跳过）
3. 确认用户Chrome已登录X

**Linux 发布（推荐）**:
```bash
# 立即发布（纯文字）
python3 scripts/post-with-schedule.py posts/category/03-post-final.md

# 立即发布（带图片）
python3 scripts/post-with-schedule.py posts/category/03-post-final.md posts/category/images/01-image.jpg

# 定时发布
python3 scripts/post-with-schedule.py posts/category/03-post-final.md \
    --schedule "2026-06-15 21:00"

# 定时发布（带图片）
python3 scripts/post-with-schedule.py posts/category/03-post-final.md \
    posts/category/images/01-image.jpg \
    --schedule "2026-06-15 21:00"
```

**macOS 发布**:
```bash
# 立即发布
bash scripts/post-with-schedule-v2.sh posts/category/03-post-final.md

# 定时发布
bash scripts/post-with-schedule-v2.sh posts/category/03-post-final.md \
    posts/category/images/01-image.jpg \
    --schedule "2026-06-15 21:00"
```

**脚本执行流程（Linux post-with-schedule.py）**:
1. 读取内容文件 → 粘贴文字到编辑器
2. (有图片时) 上传图片文件
3. 点击 Schedule post 按钮
4. (有定时时) 设置日期时间并点击 Confirm
5. 显示页面预览 → 等待用户手动确认 Post/Schedule 按钮

**时间格式**: `YYYY-MM-DD HH:MM`，24小时制，**保留前导零**（如 `05`、`09`）

**重要注意事项**:
1. **必须使用用户已登录的Chrome** - 脚本不打开新窗口
2. **Linux需安装Playwright**: `pip3 install playwright && playwright install chromium`
3. **定时后手动确认** - 脚本设置完时间后需用户手动点击最终发布按钮
4. **前导零保留** - 时间格式为 `09:00` 而非 `9:00`，与X的select value匹配

**降级方案**: 脚本失败时，提示用户手动在浏览器中操作


## 文件存储结构

```
x-post-project/
├── trending-categories.json          # 热门分类数据
├── selected-categories.json          # 用户选择的分类
├── workflow-state.json               # 工作流状态
├── posts/
│   ├── {category-slug}/
│   │   ├── category-posts.json       # 该分类下的热门帖子
│   │   ├── selected-posts.json       # 用户选择的帖子
│   │   ├── 01-post-rewritten.md      # 仿写内容
│   │   ├── 02-post-humanized.md      # 去AI痕迹后的内容
│   │   ├── 03-post-final.md          # 最终发布内容 (纯文字)
│   │   └── images/
│   │       ├── search-keyword.md     # 图片搜索关键词
│   │       ├── 01-image.jpg          # 下载的配图
│   │       └── 02-image.jpg          # 第二张配图 (可选)
│   └── ...
└── logs/
    └── workflow.log                  # 工作流日志
```

## 用户交互点汇总

| 步骤 | 交互类型 | 问题内容 |
|-----|---------|---------|
| Step 2 | 帖子选择 | 从热门帖子中选择要仿写的 |
| Step 7 | 时间设置 | 选择发布时间 |

## 错误处理策略

| 错误类型 | 处理方式 | 回滚机制 |
|---------|---------|---------|
| Exa搜索失败 | 尝试bird CLI | 记录错误，跳过当前分类 |
| bird CLI失败 | 提示用户检查登录状态 | 保留已完成内容 |
| 仿写不像真实帖文 | 重新仿写，使用不同表达 | 保留原帖备份 |
| 图片下载失败 | 使用已有图片 | 继续发布纯文字内容 |
| AppleScript失败 (macOS) | 简化脚本，避免特殊字符 | 手动操作发布 |
| Playwright失败 (Linux) | 降级到手动操作 | 用户手动发布 |
| Chrome未登录 | 使用用户已打开的Chrome | 提示用户登录 |

## 关键工具路径

| 工具 | 路径/命令 |
|------|----------|
| Exa搜索 | `mcporter call 'exa.web_search_exa(...)'` |
| bird CLI | `bird` (PATH中) |
| humanizer | `skills/humanizer-skill/SKILL.md` |
| x-post-scheduler | `x-post-scheduler` skill |
| Unsplash API | `https://api.unsplash.com/` |
| 字数检查 | `scripts/check-char-count.py` |
| 发布脚本(Linux) | `scripts/post-with-schedule.py` |
| 发布脚本(macOS) | `scripts/post-with-schedule-v2.sh` |

## 验证方法

### 1. 内容验证
- 检查帖子是否为真实用户内容 (非AI生成的摘要)
- 确认仿写保持客观事实
- 验证人性化处理去除了AI痕迹

### 2. 文件验证
- 检查所有JSON文件格式正确
- 确认03-post-final.md为纯文字 (无标题/说明)
- 验证配图文件存在且可读

### 3. 发布验证
- 确认使用用户已登录的Chrome
- 验证定时时间设置正确
- 检查页面显示 "Will send on [日期] at [时间]"

## 最佳实践

1. **内容抓取**: 优先使用Exa搜索，更可靠
2. **仿写创作**: 保持风格一致，不是简单总结
3. **配图搜索**: 优先使用Unsplash，无需API Key
4. **发布操作**: 直接操作用户已登录的Chrome，不要打开新窗口
5. **定时设置**: 使用24小时制，月份不补零
6. **错误恢复**: 保留所有中间文件，支持断点续传

## 更新日志

### 2026-06-15
- 新增Linux版发布脚本 `post-with-schedule.py` (基于Playwright)
- 修复日期时间前导零Bug (原 `sed 's/^0//'` 会导致 `09:00` → `9:00` 不匹配X的select value)
- 移除所有硬编码 `/Users/piaoxian/` 路径
- 新增 `check-char-count.py` 字数检查脚本
- 统一脚本到 `scripts/` 目录，去除重复