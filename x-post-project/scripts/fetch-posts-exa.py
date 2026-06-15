#!/usr/bin/env python3
"""
X平台热门帖子获取脚本（使用Exa搜索）
从X平台抓取热门帖子，用于内容创作
"""

import json
import subprocess
import sys
from datetime import datetime

def search_x_posts(query, count=5):
    """使用Exa搜索X平台帖子"""
    try:
        # 使用mcporter调用Exa搜索
        cmd = [
            "mcporter", "call",
            f'exa.web_search_exa(query: "{query}", numResults: {count})'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"搜索失败: {result.stderr}", file=sys.stderr)
            return []

        # 解析搜索结果
        posts = []
        lines = result.stdout.split('\n')

        current_post = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Title:'):
                if current_post:
                    posts.append(current_post)
                current_post = {
                    'title': line[6:].strip(),
                    'content': '',
                    'url': '',
                    'source': 'exa_search'
                }
            elif line.startswith('URL:'):
                current_post['url'] = line[4:].strip()
            elif line.startswith('Highlights:'):
                # 下一行开始是内容
                continue
            elif line and not line.startswith(('Published:', 'Author:')):
                current_post['content'] += line + '\n'

        if current_post:
            posts.append(current_post)

        return posts[:count]

    except subprocess.TimeoutExpired:
        print("搜索超时", file=sys.stderr)
        return []
    except Exception as e:
        print(f"搜索错误: {e}", file=sys.stderr)
        return []

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 fetch-posts-exa.py <搜索关键词> [数量]")
        sys.exit(1)

    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    # 添加lang:en过滤英文内容
    if "lang:" not in query:
        query += " lang:en"

    posts = search_x_posts(query, count)

    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "exa_search",
        "query": query,
        "count": len(posts),
        "posts": posts
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()