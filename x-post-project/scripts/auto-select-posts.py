#!/usr/bin/env python3
"""
自动从抓取的帖子中选择最优帖子

输入: fetch-posts.py 的 JSON 输出
输出: posts/{category}/selected-posts.json
"""

import json
import math
import sys
import os
from datetime import datetime

def compute_post_score(post: dict) -> float:
    """
    计算帖子综合评分

    评分维度:
    - engagement_score: 加权互动分（likes + retweets*2 + replies*3）
    - content_quality_score: 内容质量分（无链接/无RT，含数字，长度适中）

    返回: 0-10分的综合评分
    """
    likes = post.get("likes", 0)
    retweets = post.get("retweets", 0)
    replies = post.get("replies", 0)
    content = post.get("content", "")

    # 1. 加权互动分（使用对数平滑避免极端值影响）
    engagement = (
        math.log1p(likes) * 1.0 +
        math.log1p(retweets) * 2.0 +
        math.log1p(replies) * 3.0
    )

    # 2. 内容质量分
    quality = 0.0

    # 扣分：包含链接或RT格式
    if "http" in content or "RT @" in content:
        quality -= 5.0

    # 加分：包含数字（更具体）
    if any(c.isdigit() for c in content):
        quality += 1.0

    # 加分：内容长度适中（60-200字，X平台最佳长度）
    if 60 <= len(content.strip()) <= 200:
        quality += 1.5

    # 加分：避免过度使用感叹号或问号
    if content.count('!') > 3 or content.count('?') > 3:
        quality -= 0.5

    # 3. 综合得分（满分10分，截断到[0, 10]）
    raw_score = engagement * 0.6 + quality
    return max(0.0, min(10.0, raw_score))

def select_top_posts(all_posts: list, top_n: int = 5) -> list:
    """
    从帖子列表中自动选择最优的N篇

    策略:
    1. 过滤低质量帖子（链接帖子、RT格式、太短的帖子）
    2. 计算评分
    3. 按评分降序排列
    4. 取前top_n篇
    5. 如果不够top_n篇，放宽过滤条件重试
    """

    # Step 1: 过滤低质量帖子
    filtered = []
    for post in all_posts:
        content = post.get("content", "")
        # 跳过明显是广告或RT的帖子
        if "http" in content and len(content) < 50:
            continue
        if "RT @" in content:
            continue
        if len(content.strip()) < 20:  # 太短的帖子
            continue
        filtered.append(post)

    if not filtered:
        print("[WARN] 所有帖子都被过滤，使用原始列表", file=sys.stderr)
        filtered = all_posts

    # Step 2: 评分
    scored = [(compute_post_score(p), p) for p in filtered]

    # Step 3: 按评分降序排列
    scored.sort(key=lambda x: x[0], reverse=True)

    # Step 4: 取前N篇
    selected = [p for _, p in scored[:top_n]]

    # Step 5: 如果不够，放宽条件重试
    if len(selected) < top_n and len(filtered) > 0:
        print(f"[WARN] 只找到 {len(selected)} 篇优质帖子，放宽条件补充", file=sys.stderr)

        # 放宽过滤条件：只过滤RT和链接，不限制长度
        relaxed = [p for p in all_posts
                  if "RT @" not in p.get("content", "")]

        scored = [(compute_post_score(p), p) for p in relaxed]
        scored.sort(key=lambda x: x[0], reverse=True)

        # 补充到目标数量
        remaining = top_n - len(selected)
        additional = [p for _, p in scored[:remaining]]
        selected.extend(additional)

        # 去重
        seen_ids = set(p["id"] for p in selected)
        selected = [p for p in selected if p["id"] not in seen_ids]

    return selected[:top_n]

def main():
    if len(sys.argv) < 2:
        print("Usage: auto-select-posts.py <input_json_file> <output_json_file> [top_n]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    posts = data.get("posts", [])

    if not posts:
        print("[ERROR] 输入文件中没有帖子数据", file=sys.stderr)
        sys.exit(1)

    # 自动选择
    selected_posts = select_top_posts(posts, top_n)

    # 输出结果
    output_data = {
        "selected_at": datetime.now().isoformat(),
        "total_posts": len(posts),
        "selected_count": len(selected_posts),
        "top_n": top_n,
        "posts": selected_posts
    }

    # 创建输出目录
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"成功选择 {len(selected_posts)} 篇帖子到 {output_file}", file=sys.stderr)

if __name__ == "__main__":
    main()