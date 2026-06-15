#!/usr/bin/env python3
"""
生成发布预览文件 AUTO-PREVIEW.md

输入: workflow-state.json
输出: AUTO-PREVIEW.md
"""

import json
import os
import sys
from datetime import datetime

def generate_preview(workflow_state_file: str, output_file: str) -> None:
    """
    生成用户预览文件

    预览包含:
    - 总体统计（总帖数、分类数、总字符数）
    - 每篇帖子的：分类、内容、配图预览路径、字符数、计划发布时间
    - 一键确认命令
    """

    # 读取工作流状态
    with open(workflow_state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # 检查必要字段
    if "posts" not in state:
        print("[ERROR] workflow-state.json 中缺少 posts 字段", file=sys.stderr)
        sys.exit(1)

    posts = state["posts"]
    if not posts:
        print("[ERROR] 没有待发布的帖子", file=sys.stderr)
        sys.exit(1)

    # 生成预览内容
    lines = [
        "# X 帖子发布预览",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**总帖子数**: {len(posts)}",
        f"**定时发布**: 从 {state.get('schedule_config', {}).get('start_time', '未知')} 开始，间隔 {state.get('schedule_config', {}).get('interval_minutes', 15)} 分钟",
        "",
        "---",
    ]

    # 逐篇生成预览
    for post in posts:
        lines += [
            f"## [{post['category']}] 帖子 {post['index_in_category']}",
            f"**内容文件**: `{post['content_file']}`",
            f"**配图文件**: `{post['image_file'] or '无'}`",
            f"**计划发布时间**: {post['schedule_time']}",
            f"**字符数**: {post['char_count']} / 280",
            "",
            "**内容预览**:",
            "```",
            post['content'],
            "```",
            "",
            "---",
        ]

    # 添加确认指令
    lines += [
        "## 发布确认",
        "",
        "**确认发布**: 回复 `confirm` 或 `ok` 即可开始发布",
        "**修改内容**: 回复 `edit {编号}` 进入修改指定帖子（如 edit 3）",
        "**取消**: 回复 `cancel` 取消本次发布",
        "",
        "---",
        "*此文件由自动工作流生成，内容已通过字数检查和人性化处理*",
    ]

    # 写入文件
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"预览文件已生成: {output_file}", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: generate-preview.py <workflow_state_file> [output_file]", file=sys.stderr)
        sys.exit(1)

    workflow_state_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "/Users/piaoxian/x-post-project/AUTO-PREVIEW.md"

    generate_preview(workflow_state_file, output_file)

if __name__ == "__main__":
    main()