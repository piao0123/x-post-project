#!/usr/bin/env python3
"""
获取X平台热门帖子（优化版）
使用多种方式获取真实用户帖子
"""

import json
import subprocess
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import urlencode

def fetch_posts_via_bird(keyword, count=5):
    """
    使用bird search获取真实用户帖子（英文内容）

    Args:
        keyword: 搜索关键词（英文）
        count: 获取的帖子数量

    Returns:
        list: 热门帖子列表
    """
    try:
        # 使用英文关键词搜索，过滤高赞帖子
        # 添加lang:en确保是英文内容
        # 使用min_faves:100获取更热门的帖子
        # 注意：bird search的查询是一个字符串，不是多个参数
        query = f"{keyword} lang:en min_faves:100 -filter:links -filter:replies"
        cmd = ["bird", "search", "-n", str(count), "--json", query]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"bird search failed: {result.stderr}", file=sys.stderr)
            return []

        # 解析JSON输出
        try:
            data = json.loads(result.stdout)
            posts = []

            if isinstance(data, list):
                for item in data:
                    # 过滤掉链接和回复，确保是原创帖子
                    text = item.get('text', '')
                    if 'http' in text or 'RT @' in text:
                        continue

                    post = {
                        'id': item.get('id', ''),
                        'author': item.get('author', {}).get('username', ''),
                        'content': text,
                        'likes': item.get('likes', 0),
                        'retweets': item.get('retweets', 0),
                        'replies': item.get('replies', 0),
                        'created_at': item.get('created_at', ''),
                        'url': item.get('url', ''),
                        'media': [m.get('url', '') for m in item.get('media', [])]
                    }
                    posts.append(post)

            return posts[:count]

        except json.JSONDecodeError as e:
            print(f"Failed to parse bird output: {e}", file=sys.stderr)
            return []

    except subprocess.TimeoutExpired:
        print("bird search timed out", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("bird command not found", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching posts via bird: {e}", file=sys.stderr)
        return []

def fetch_posts_via_exa(keyword, count=5):
    """
    使用Exa搜索获取Twitter帖子（英文内容）

    Args:
        keyword: 搜索关键词（英文）
        count: 获取的帖子数量

    Returns:
        list: 热门帖子列表
    """
    try:
        # 优化搜索查询，专注于英文Twitter帖子
        query = f"site:twitter.com OR site:x.com {keyword} lang:en -site:help.x.com -site:docs.x.com"
        cmd = [
            "mcporter", "call",
            f"exa.web_search_exa(query: \"{query}\", numResults: {count * 2})"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"mcporter search failed: {result.stderr}", file=sys.stderr)
            return []

        # 解析输出，过滤出真实帖子
        posts = []
        lines = result.stdout.strip().split('\n')

        for i, line in enumerate(lines):
            if line.startswith('Title:'):
                title = line[6:].strip()

                # 提取URL（下一行）
                if i + 1 < len(lines) and lines[i + 1].startswith('URL:'):
                    url = lines[i + 1][4:].strip()

                    # 过滤掉帮助文档和FAQ
                    if any(x in url for x in ['help.x.com', 'docs.x.com', 'support.x.com']):
                        continue

                    # 过滤掉非帖子内容
                    if any(x in title.lower() for x in ['faq', 'help', 'guide', 'tutorial', 'how to']):
                        continue

                    # 构建帖子信息
                    post = {
                        'id': f"exa_{i}",
                        'author': '',
                        'content': title,
                        'likes': 0,
                        'retweets': 0,
                        'replies': 0,
                        'created_at': '',
                        'url': url,
                        'media': []
                    }
                    posts.append(post)

                    if len(posts) >= count:
                        break

        return posts[:count]

    except subprocess.TimeoutExpired:
        print("mcporter search timed out", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("mcporter command not found", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching posts via Exa: {e}", file=sys.stderr)
        return []

def fetch_posts_via_twitter_api(keyword, count=5):
    """
    使用Twitter API v2获取帖子（需要付费套餐）

    Args:
        keyword: 搜索关键词
        count: 获取的帖子数量

    Returns:
        list: 热门帖子列表
    """
    try:
        import os
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        if not bearer_token:
            print("TWITTER_BEARER_TOKEN not set", file=sys.stderr)
            return []

        import requests
        proxy = os.environ.get('https_proxy') or os.environ.get('http_proxy')
        proxies = {"http": proxy, "https": proxy} if proxy else None

        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {
            "query": f"{keyword} lang:en -is:retweet -is:reply",
            "max_results": min(count, 10),
            "tweet.fields": "created_at,public_metrics,author_id"
        }

        response = requests.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers=headers,
            params=params,
            timeout=15,
            proxies=proxies
        )

        if response.status_code == 200:
            data = response.json()
            posts = []
            for tweet in data.get('data', []):
                metrics = tweet.get('public_metrics', {})
                posts.append({
                    'id': tweet.get('id', ''),
                    'author': tweet.get('author_id', ''),
                    'content': tweet.get('text', ''),
                    'likes': metrics.get('like_count', 0),
                    'retweets': metrics.get('retweet_count', 0),
                    'replies': metrics.get('reply_count', 0),
                    'created_at': tweet.get('created_at', ''),
                    'url': f"https://twitter.com/i/status/{tweet.get('id', '')}",
                    'media': []
                })
            return posts[:count]
        else:
            print(f"Twitter API error: {response.status_code}", file=sys.stderr)
            return []

    except Exception as e:
        print(f"Error fetching posts via Twitter API: {e}", file=sys.stderr)
        return []

def fetch_posts(keyword, count=5):
    """
    获取热门帖子（优先使用Exa，备选bird和Twitter API）

    Args:
        keyword: 搜索关键词
        count: 获取的帖子数量

    Returns:
        list: 热门帖子列表
    """
    # 优先使用Exa搜索（最可靠）
    posts = fetch_posts_via_exa(keyword, count)

    # 如果Exa失败，尝试bird search
    if not posts:
        print("Exa search failed, trying bird...", file=sys.stderr)
        posts = fetch_posts_via_bird(keyword, count)

    # 如果bird也失败，尝试Twitter API
    if not posts:
        print("bird search failed, trying Twitter API...", file=sys.stderr)
        posts = fetch_posts_via_twitter_api(keyword, count)

    return posts

def main():
    if len(sys.argv) < 2:
        print("Usage: fetch-posts.py <keyword> [count]", file=sys.stderr)
        sys.exit(1)

    keyword = sys.argv[1]
    count = 5
    if len(sys.argv) > 2:
        try:
            count = int(sys.argv[2])
        except ValueError:
            print(f"Invalid count: {sys.argv[2]}, using default 5", file=sys.stderr)

    # 获取热门帖子
    posts = fetch_posts(keyword, count)

    if not posts:
        print(f"No posts found for keyword: {keyword}", file=sys.stderr)
        sys.exit(1)

    # 构建输出数据
    output = {
        "fetched_at": datetime.now().isoformat(),
        "keyword": keyword,
        "posts": posts
    }

    # 输出JSON
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
