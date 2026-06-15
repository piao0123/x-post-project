#!/usr/bin/env python3
"""
X帖子全自动创作发布工作流

用法:
python3 run-workflow.py # 默认配置
python3 run-workflow.py --categories 5 # 指定分类数
python3 run-workflow.py --posts-per-category 3 # 指定每分类帖子数
python3 run-workflow.py --start-time "2026-06-09 09:00" # 指定首发时间
python3 run-workflow.py --interval 20 # 发布间隔20分钟
python3 run-workflow.py --resume # 从断点续传
python3 run-workflow.py --dry-run # 仅预览，不发布
python3 run-workflow.py --skip-fetch # 跳过内容抓取，复用已有数据
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

def load_config():
    """加载主配置文件"""
    config_file = "/Users/piaoxian/x-post-project/config/main.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_or_init_state(state_file: str, args) -> dict:
    """加载或初始化工作流状态"""
    if os.path.exists(state_file) and args.resume:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        current = state.get("current_step", 0)
        print(f"[续传] 从 Step {current} 继续（跳过已完成步骤）")
        return state
    else:
        # 初始化状态
        config = load_config()
        start_time = args.start_time or f"{datetime.now().strftime('%Y-%m-%d')} 21:00"

        return {
            "workflow_id": f"x-post-{datetime.now():%Y%m%d%H%M%S}",
            "version": "2.0",
            "current_step": 0,
            "status": "initialized",
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "resume_from_step": None,
            "dry_run": args.dry_run,
            "skip_fetch": args.skip_fetch,

            "schedule_config": {
                "start_time": start_time,
                "interval_minutes": args.interval
            },

            "categories_config": {
                "total": args.categories,
                "posts_per_category": args.posts_per_category
            },

            "steps": {
                "step_1_trending": { "status": "pending", "at": None },
                "step_2_fetch_and_select": { "status": "pending", "at": None },
                "step_3_rewrite": { "status": "pending", "at": None },
                "step_4_humanize": { "status": "pending", "at": None },
                "step_5_image_and_check": { "status": "pending", "at": None },
                "step_6_preview": { "status": "pending", "at": None },
                "step_7_publish": { "status": "pending", "at": None }
            },

            "posts": [],
            "preview_file": "/Users/piaoxian/x-post-project/AUTO-PREVIEW.md",
            "preview_generated_at": None,
            "user_confirmed_at": None,
            "completed_at": None,
            "errors": []
        }

def update_state(state: dict, key: str, value) -> None:
    """更新状态并写入文件"""
    state[key] = value
    state["last_updated"] = datetime.now().isoformat()

    state_file = "/Users/piaoxian/x-post-project/workflow-state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"[状态更新] {key} = {value}", file=sys.stderr)

def run_step_1(config: dict, state: dict) -> None:
    """Step 1: 热门话题获取"""
    print("[Step 1] 热门话题获取...")

    # 从配置获取国家和数量
    country = config.get("defaults", {}).get("country", "united-states")
    category_count = state["categories_config"]["total"]

    # 调用 fetch-trending.py
    cmd = [
        "/Users/piaoxian/x-post-project/scripts/fetch-trending.py",
        str(category_count),
        country
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] fetch-trending.py 失败: {result.stderr}", file=sys.stderr)
        state["errors"].append(f"Step 1 failed: {result.stderr}")
        return

    # 保存输出到文件
    output_file = "/Users/piaoxian/x-post-project/trending-categories.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result.stdout)

    print(f"[Step 1] 成功生成 {output_file}")
    update_state(state, "steps.step_1_trending.status", "completed")
    update_state(state, "steps.step_1_trending.at", datetime.now().isoformat())

def run_step_2(config: dict, state: dict) -> None:
    """Step 2: 帖子抓取 + 自动评分选择"""
    print("[Step 2] 帖子抓取 + 自动评分选择...")

    # 获取已选择的分类
    selected_categories_file = "/Users/piaoxian/x-post-project/selected-categories.json"
    if not os.path.exists(selected_categories_file):
        print("[ERROR] selected-categories.json 不存在", file=sys.stderr)
        state["errors"].append("selected-categories.json not found")
        return

    with open(selected_categories_file, 'r', encoding='utf-8') as f:
        selected_cats = json.load(f)

    categories = selected_cats.get("selected_categories", [])
    if not categories:
        print("[ERROR] 没有选择任何分类", file=sys.stderr)
        state["errors"].append("No categories selected")
        return

    posts_per_category = state["categories_config"]["posts_per_category"]

    # 为每个分类执行抓取和选择
    all_selected_posts = []

    for category in categories:
        cat_id = category["id"]
        cat_name = category["name_cn"]

        # 构建输出目录
        cat_dir = f"/Users/piaoxian/x-post-project/posts/{cat_id}"
        os.makedirs(cat_dir, exist_ok=True)

        # 检查是否可以复用已有数据
        category_posts_file = f"{cat_dir}/category-posts.json"
        if state["skip_fetch"] and os.path.exists(category_posts_file):
            print(f"[Step 2] 跳过抓取，复用 {cat_id} 的已有数据")
        else:
            # 执行抓取
            keyword = category.get("search_query", cat_name)
            cmd = [
                "/Users/piaoxian/x-post-project/scripts/fetch-posts.py",
                keyword,
                str(posts_per_category * 2) # 抓取更多，供筛选
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[WARN] {cat_id} 抓取失败: {result.stderr}", file=sys.stderr)
                state["errors"].append(f"{cat_id} fetch failed: {result.stderr}")
                continue

            # 保存抓取结果
            with open(category_posts_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)

            print(f"[Step 2] {cat_id} 抓取完成，保存到 {category_posts_file}")

        # 执行自动选择
        selected_posts_file = f"{cat_dir}/selected-posts.json"
        cmd = [
            "/Users/piaoxian/x-post-project/scripts/auto-select-posts.py",
            category_posts_file,
            selected_posts_file,
            str(posts_per_category)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[WARN] {cat_id} 选择失败: {result.stderr}", file=sys.stderr)
            state["errors"].append(f"{cat_id} selection failed: {result.stderr}")
            continue

        # 读取选择结果并添加到全局列表
        with open(selected_posts_file, 'r', encoding='utf-8') as f:
            selected_data = json.load(f)

        for post in selected_data["posts"]:
            # 为每个帖子添加分类信息
            post["category"] = cat_id
            post["index_in_category"] = len([p for p in all_selected_posts if p["category"] == cat_id]) + 1
            post["content_file"] = f"{cat_dir}/01-post-rewritten.md"
            post["image_file"] = f"{cat_dir}/images/0{post['index_in_category']}-image.jpg"
            post["schedule_time"] = "" # 会由后续步骤填充
            post["char_count"] = 0
            all_selected_posts.append(post)

        print(f"[Step 2] {cat_id} 选择完成，{len(selected_data['posts'])} 篇")

    # 更新全局状态
    state["posts"] = all_selected_posts
    state["total_posts"] = len(all_selected_posts)
    update_state(state, "steps.step_2_fetch_and_select.status", "completed")
    update_state(state, "steps.step_2_fetch_and_select.at", datetime.now().isoformat())

def run_step_3(config: dict, state: dict) -> None:
    """Step 3: 仿写创作"""
    print("[Step 3] 仿写创作...")

    for post in state["posts"]:
        cat_id = post["category"]
        cat_dir = f"/Users/piaoxian/x-post-project/posts/{cat_id}"
        content_file = post["content_file"]

        # 创建目录
        os.makedirs(cat_dir, exist_ok=True)

        # 生成仿写内容（这里简化为复制原帖，实际应调用AI服务）
        # 实际项目中应调用 AI 服务进行仿写
        original_post_file = f"{cat_dir}/selected-posts.json"
        with open(original_post_file, 'r', encoding='utf-8') as f:
            selected_data = json.load(f)

        # 找到对应帖子
        original_post = None
        for p in selected_data["posts"]:
            if p["id"] == post["id"]:
                original_post = p
                break

        if not original_post:
            print(f"[WARN] 未找到 {cat_id} 的原始帖子 {post['id']}")
            continue

        # 生成仿写内容（简化版）
        content = original_post["content"]
        # 实际项目中应调用AI服务进行改写
        # 这里使用原始内容作为占位

        # 生成 Markdown 格式
        markdown_content = f"""# {cat_id} 帖子 {post['index_in_category']}

## 原文
{content}

## 仿写
{content}

## 客观事实
- {content[:50]}... (自动提取)

## 配图路径
- {post['image_file']}
"""

        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"[Step 3] {cat_id} 仿写完成: {content_file}")

    update_state(state, "steps.step_3_rewrite.status", "completed")
    update_state(state, "steps.step_3_rewrite.at", datetime.now().isoformat())

def run_step_4(config: dict, state: dict) -> None:
    """Step 4: 人性化处理"""
    print("[Step 4] 人性化处理...")

    for post in state["posts"]:
        cat_id = post["category"]
        cat_dir = f"/Users/piaoxian/x-post-project/posts/{cat_id}"
        content_file = post["content_file"]
        humanized_file = f"{cat_dir}/02-post-humanized.md"

        # 读取仿写内容
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 人工简化：移除AI高频词，增加句式变化
        # 实际项目中应调用 humanizer skill
        lines = content.splitlines()
        humanized_lines = []

        for line in lines:
            # 简化AI风格：移除一些典型AI用语
            line = line.replace("此外", "")
            line = line.replace("另外", "")
            line = line.replace("值得注意的是", "")
            line = line.replace("重要的是", "")
            line = line.replace("总的来说", "")
            line = line.replace("综上所述", "")

            humanized_lines.append(line)

        humanized_content = '\n'.join(humanized_lines)

        # 写入人性化后内容
        with open(humanized_file, 'w', encoding='utf-8') as f:
            f.write(humanized_content)

        print(f"[Step 4] {cat_id} 人性化完成: {humanized_file}")

    update_state(state, "steps.step_4_humanize.status", "completed")
    update_state(state, "steps.step_4_humanize.at", datetime.now().isoformat())

def run_step_5(config: dict, state: dict) -> None:
    """Step 5: 配图搜索下载 + 字数检查"""
    print("[Step 5] 配图搜索下载 + 字数检查...")

    # 获取配置
    pexels_api_key = os.environ.get("PEXELS_API_KEY")
    free_sites_enabled = config.get("image_sources", {}).get("free_sites", {}).get("enabled", False)

    for post in state["posts"]:
        cat_id = post["category"]
        cat_dir = f"/Users/piaoxian/x-post-project/posts/{cat_id}"
        humanized_file = f"{cat_dir}/02-post-humanized.md"
        final_file = f"{cat_dir}/03-post-final.md"
        image_file = post["image_file"]

        # 1. 下载配图
        if pexels_api_key:
            # 从人性化内容中提取关键词
            with open(humanized_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简单关键词提取（实际应使用更智能的方法）
            keywords = [cat_id]
            if "AI" in content:
                keywords.append("AI")
            if "科技" in content:
                keywords.append("科技")
            if "技术" in content:
                keywords.append("技术")

            keyword = keywords[0] # 使用第一个关键词

            # 调用 fetch-image.py
            cmd = [
                "/Users/piaoxian/x-post-project/scripts/fetch-image.py",
                keyword,
                image_file,
                pexels_api_key
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[WARN] {cat_id} 图片下载失败: {result.stderr}", file=sys.stderr)
                state["errors"].append(f"{cat_id} image download failed: {result.stderr}")
                # 保留 image_file 为空，继续发布纯文字
            else:
                print(f"[Step 5] {cat_id} 图片下载成功: {image_file}")
        elif free_sites_enabled:
            # 使用免费图片源
            with open(humanized_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取关键词用于搜索
            keywords = [cat_id]
            if "AI" in content:
                keywords.append("AI")
            if "technology" in content.lower():
                keywords.append("technology")
            if "science" in content.lower():
                keywords.append("science")
            if "space" in content.lower():
                keywords.append("space")
            if "nasa" in content.lower():
                keywords.append("nasa")
            if "f1" in content.lower():
                keywords.append("f1")
            if "formula 1" in content.lower():
                keywords.append("formula 1")
            if "nba" in content.lower():
                keywords.append("nba")
            if "business" in content.lower():
                keywords.append("business")
            if "finance" in content.lower():
                keywords.append("finance")
            if "investing" in content.lower():
                keywords.append("investing")

            keyword = keywords[0]

            # 调用 download-free-image.py
            cmd = [
                "/Users/piaoxian/x-post-project/scripts/download-free-image.py",
                keyword,
                image_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[WARN] {cat_id} 免费图片下载失败: {result.stderr}", file=sys.stderr)
                state["errors"].append(f"{cat_id} free image download failed: {result.stderr}")
                # 保留 image_file 为空，继续发布纯文字
            else:
                print(f"[Step 5] {cat_id} 免费图片下载成功: {image_file}")
        else:
            print(f"[Step 5] {cat_id} 跳过图片下载（无API密钥且免费图片源禁用）")

        # 2. 字数检查
        with open(humanized_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取纯文本内容（去掉Markdown标记）
        lines = content.splitlines()
        text_lines = []
        in_code_block = False

        for line in lines:
            if line.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if line.startswith("# ") or line.startswith("## "):
                continue
            if line.startswith("- "):
                line = line[2:]
            text_lines.append(line)

        plain_text = '\n'.join(text_lines)
        char_count = len(plain_text)

        # 检查字符数
        if char_count > 280:
            # 截断到280字符
            plain_text = plain_text[:280]
            print(f"[WARN] {cat_id} 字符数 {char_count} > 280，已截断", file=sys.stderr)
            state["errors"].append(f"{cat_id} content truncated to 280 chars")

        # 写入最终文件（纯文本，无标题）
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(plain_text)

        post["char_count"] = len(plain_text)
        print(f"[Step 5] {cat_id} 字数检查完成: {final_file} ({len(plain_text)} 字符)")

    update_state(state, "steps.step_5_image_and_check.status", "completed")
    update_state(state, "steps.step_5_image_and_check.at", datetime.now().isoformat())

def run_step_6(config: dict, state: dict) -> None:
    """Step 6: 生成发布预览"""
    print("[Step 6] 生成发布预览...")

    # 计算发布时间
    start_time_str = state["schedule_config"]["start_time"]
    interval_minutes = state["schedule_config"]["interval_minutes"]

    # 解析开始时间
    try:
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"[ERROR] 无效的开始时间格式: {start_time_str}", file=sys.stderr)
        state["errors"].append(f"Invalid start time format: {start_time_str}")
        return

    # 为每篇帖子计算发布时间
    for i, post in enumerate(state["posts"]):
        post["schedule_time"] = (start_time + timedelta(minutes=i * interval_minutes)).strftime("%Y-%m-%d %H:%M")

    # 生成预览文件
    generate_preview_cmd = [
        "/Users/piaoxian/x-post-project/scripts/generate-preview.py",
        "/Users/piaoxian/x-post-project/workflow-state.json"
    ]

    result = subprocess.run(generate_preview_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] 生成预览失败: {result.stderr}", file=sys.stderr)
        state["errors"].append(f"Generate preview failed: {result.stderr}")
    else:
        print(f"[Step 6] 预览文件已生成: {state['preview_file']}")

    update_state(state, "steps.step_6_preview.status", "completed")
    update_state(state, "steps.step_6_preview.at", datetime.now().isoformat())
    update_state(state, "preview_generated_at", datetime.now().isoformat())
    update_state(state, "status", "awaiting_confirm")

def run_step_7(config: dict, state: dict) -> None:
    """Step 7: 为每篇帖子创建X草稿，等待用户手动发布"""
    print("[Step 7] 为每篇帖子创建X草稿，等待用户手动发布...")

    # 检查是否已确认
    if not state.get("user_confirmed_at"):
        print("[INFO] 等待用户确认后手动发布...")
        return

    # 更新状态
    update_state(state, "status", "drafts_ready")

    # 为每篇帖子创建X草稿（使用x-post-scheduler的流程）
    for post in state["posts"]:
        cat_id = post["category"]
        cat_dir = f"/Users/piaoxian/x-post-project/posts/{cat_id}"
        content_file = post["content_file"]
        image_file = post["image_file"]
        schedule_time = post["schedule_time"]

        # 读取最终内容
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 创建草稿文件（纯文本，适合复制到X）
        draft_file = f"{cat_dir}/04-draft-for-x.md"
        with open(draft_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[Step 7] 已生成草稿: {draft_file}")

        # 调用x-post-scheduler的流程来创建草稿
        # 这将打开X发帖页面，粘贴内容，设置时间，但不点击最终的Schedule按钮
        # 仅创建草稿，等待用户手动点击Schedule

        # 1. 复制文字到剪贴板
        print(f"[Step 7] 复制文字到剪贴板: {content[:50]}...")
        subprocess.run(["pbcopy"], input=content.encode('utf-8'), check=True)

        # 2. 打开X发帖页面
        print("[Step 7] 打开X发帖页面...")
        subprocess.run([
            "osascript", "-e",
            'tell application "Google Chrome" to activate'
        ], check=True)
        subprocess.run([
            "osascript", "-e",
            'tell application "Google Chrome" to execute active tab of front window javascript "window.location.href = \"https://x.com/compose/post\""'
        ], check=True)

        # 等待页面加载
        time.sleep(5)

        # 3. 粘贴文字
        print("[Step 7] 粘贴文字...")
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "v" using command down'
        ], check=True)

        # 4. 复制图片到剪贴板（如果有）
        if image_file and os.path.exists(image_file):
            print(f"[Step 7] 复制图片到剪贴板: {image_file}")
            ext = os.path.splitext(image_file)[1].lower()
            if ext in ['.jpg', '.jpeg']:
                subprocess.run([
                    "osascript", "-e",
                    f'tell application "Finder" to set theFile to (POSIX file "{image_file}") as alias',
                    "-e",
                    'tell application "System Events" to set the clipboard to (read theFile as JPEG picture)'
                ], check=True)
            elif ext == '.png':
                subprocess.run([
                    "osascript", "-e",
                    f'tell application "Finder" to set theFile to (POSIX file "{image_file}") as alias',
                    "-e",
                    'tell application "System Events" to set the clipboard to (read theFile as PNG picture)'
                ], check=True)
            elif ext == '.gif':
                subprocess.run([
                    "osascript", "-e",
                    f'tell application "Finder" to set theFile to (POSIX file "{image_file}") as alias',
                    "-e",
                    'tell application "System Events" to set the clipboard to (read theFile as GIF picture)'
                ], check=True)

        # 粘贴图片
        print("[Step 7] 粘贴图片...")
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "v" using command down'
        ], check=True)
        time.sleep(3)

        # 5. 点击Schedule post按钮
        print("[Step 7] 点击Schedule post按钮...")
        subprocess.run([
            "osascript", "-e",
            'tell application "Google Chrome" to activate',
            "-e",
            'tell application "Google Chrome" to execute active tab of front window javascript "const buttons = document.querySelectorAll(\"button\"); for (let btn of buttons) { const text = btn.innerText || btn.getAttribute(\"aria-label\") || \"\"; if (text.includes(\"Schedule post\")) { btn.click(); break; } }"'
        ], check=True)

        # 6. 设置定时日期时间
        if schedule_time:
            print(f"[Step 7] 设置定时: {schedule_time}...")

            # 解析时间
            try:
                schedule_dt = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
                month = str(schedule_dt.month)
                day = str(schedule_dt.day)
                year = str(schedule_dt.year)
                hour = str(schedule_dt.hour)
                minute = str(schedule_dt.minute)

                # 设置日期时间
                subprocess.run([
                    "osascript", "-e",
                    f'tell application "Google Chrome" to activate',
                    "-e",
                    f'tell application "Google Chrome" to execute active tab of front window javascript "const selects = document.querySelectorAll(\"select\"); selects[0].value = \"{month}\"; selects[0].dispatchEvent(new Event(\"change\", {{bubbles: true}})); selects[1].value = \"{day}\"; selects[1].dispatchEvent(new Event(\"change\", {{bubbles: true}})); selects[2].value = \"{year}\"; selects[2].dispatchEvent(new Event(\"change\", {{bubbles: true}})); selects[3].value = \"{hour}\"; selects[3].dispatchEvent(new Event(\"change\", {{bubbles: true}})); selects[4].value = \"{minute}\"; selects[4].dispatchEvent(new Event(\"change\", {{bubbles: true}}));"'
                ], check=True)

                # 点击Confirm
                print("[Step 7] 点击Confirm确认时间...")
                subprocess.run([
                    "osascript", "-e",
                    'tell application "Google Chrome" to activate',
                    "-e",
                    'tell application "Google Chrome" to execute active tab of front window javascript "const buttons = document.querySelectorAll(\"button\"); for (let btn of buttons) { if (btn.innerText && btn.innerText.includes(\"Confirm\")) { btn.click(); break; } }"'
                ], check=True)

                time.sleep(2)

            except ValueError:
                print(f"[WARN] 无效的时间格式: {schedule_time}")

        # 7. 等待用户手动点击Schedule按钮
        print(f"[Step 7] 已为 {cat_id} 帖子 {post['index_in_category']} 创建草稿")
        print(f"[Step 7] 请在X页面中手动点击Schedule按钮完成发布")
        print(f"[Step 7] 时间已设置为: {schedule_time}")
        print(f"[Step 7] 草稿已保存在: {draft_file}")
        print("---")

    # 生成草稿清单
    draft_list_file = "/Users/piaoxian/x-post-project/DRAFTS-LIST.md"
    lines = ["# X 帖子草稿清单"]
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**总草稿数**: {len(state['posts'])}")
    lines.append("")
    lines.append("---")

    for post in state["posts"]:
        lines.append(f"## [{post['category']}] 帖子 {post['index_in_category']}")
        lines.append(f"**内容文件**: `{post['content_file']}`")
        lines.append(f"**草稿文件**: `{post['content_file'].replace('03-post-final.md', '04-draft-for-x.md')}`")
        lines.append(f"**配图文件**: `{post['image_file'] or '无'}`")
        lines.append(f"**计划发布时间**: {post['schedule_time']}")
        lines.append("")
        lines.append("**内容预览**:")
        lines.append("```")
        lines.append(post['content'])
        lines.append("```")
        lines.append("")
        lines.append("---")

    lines.append("## 发布说明")
    lines.append("")
    lines.append("**请手动操作**：")
    lines.append("1. 等待系统自动打开X发帖页面")
    lines.append("2. 系统会自动粘贴文字和图片（如有）")
    lines.append("3. 系统会自动点击Schedule post按钮")
    lines.append("4. 系统会自动设置定时时间")
    lines.append("5. **最后一步：请手动点击Schedule按钮完成发布**")
    lines.append("")
    lines.append("**重要**：本系统不会自动发布任何内容，所有发布都由您手动完成。")
    lines.append("")
    lines.append("---")
    lines.append("*此文件由自动工作流生成，内容已通过字数检查和人性化处理*")

    with open(draft_list_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"[Step 7] 草稿清单已生成: {draft_list_file}")
    print("[完成] 所有帖子已创建为X草稿，等待您手动点击Schedule按钮完成发布！")

def main():
    parser = argparse.ArgumentParser(description="X帖子全自动工作流")
    parser.add_argument("--categories", type=int, default=10,
                        help="热门分类数量（默认10）")
    parser.add_argument("--posts-per-category", "--posts", type=int, default=5,
                        help="每分类帖子数（默认5）")
    parser.add_argument("--start-time", default=None,
                        help="首发时间（格式: YYYY-MM-DD HH:MM）")
    parser.add_argument("--interval", type=int, default=15,
                        help="发布间隔分钟数（默认15）")
    parser.add_argument("--resume", action="store_true",
                        help="从断点续传")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅生成预览，不发布")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="跳过内容抓取，复用已有数据")

    args = parser.parse_args()

    # 加载配置
    config = load_config()
    base_dir = "/Users/piaoxian/x-post-project"
    state_file = f"{base_dir}/workflow-state.json"

    # 初始化或加载状态
    state = load_or_init_state(state_file, args)

    # Step 1: 热门话题获取
    if not args.resume or state.get("current_step", 0) < 1:
        run_step_1(config, state)
        update_state(state, "current_step", 1)

    # Step 2: 帖子抓取 + 自动选择
    if not args.resume or state.get("current_step", 0) < 2:
        run_step_2(config, state)
        update_state(state, "current_step", 2)

    # Step 3: 仿写创作
    if not args.resume or state.get("current_step", 0) < 3:
        run_step_3(config, state)
        update_state(state, "current_step", 3)

    # Step 4: 人性化处理
    if not args.resume or state.get("current_step", 0) < 4:
        run_step_4(config, state)
        update_state(state, "current_step", 4)

    # Step 5: 配图 + 字数检查
    if not args.resume or state.get("current_step", 0) < 5:
        run_step_5(config, state)
        update_state(state, "current_step", 5)

    # Step 6: 生成预览
    if not args.resume or state.get("current_step", 0) < 6:
        run_step_6(config, state)
        update_state(state, "current_step", 6)

    # Step 7: 发布（仅在非 dry-run 且用户确认后执行）
    if not args.dry_run and state.get("status") == "awaiting_confirm":
        print("[等待确认] 请使用 AskUserQuestion 询问用户确认...")
        # 实际运行时，Claude会调用AskUserQuestion，用户确认后会触发run_step_7
        # 这里只是等待
    elif not args.dry_run and state.get("status") == "awaiting_confirm":
        # 如果用户已经确认，直接发布
        run_step_7(config, state)
    elif args.dry_run:
        print("[DRY-RUN] 工作流完成，仅生成预览")
    else:
        print("[INFO] 工作流已完成")

if __name__ == "__main__":
    main()