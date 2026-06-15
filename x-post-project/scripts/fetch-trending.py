#!/usr/bin/env python3
"""
获取X平台热门话题分类
使用xtrends网站的数据
"""

import json
import re
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from html import unescape

def fetch_trending_topics(country="united-states", count=10):
    """
    从xtrends网站获取热门话题

    Args:
        country: 国家代码（如 united-states, worldwide）
        count: 获取的话题数量

    Returns:
        list: 热门话题列表
    """
    url = f"https://xtrends.in/{country}/"

    try:
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = Request(url, headers=headers)

        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # 从JSON-LD中提取热门话题
        json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
        json_ld_matches = re.findall(json_ld_pattern, html, re.DOTALL)

        trending_topics = []
        for match in json_ld_matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and 'mainEntity' in data:
                    main_entity = data['mainEntity']
                    if isinstance(main_entity, dict) and 'itemListElement' in main_entity:
                        for item in main_entity['itemListElement']:
                            if isinstance(item, dict) and 'name' in item:
                                topic = {
                                    'headline': item['name'],
                                    'url': item.get('url', ''),
                                    'category': 'trending',
                                    'postCount': None,
                                    'timeAgo': 'just now'
                                }
                                trending_topics.append(topic)
            except json.JSONDecodeError:
                continue

        # 限制返回数量
        return trending_topics[:count]

    except Exception as e:
        print(f"Error fetching trending topics: {e}", file=sys.stderr)
        return []

def main():
    # 默认获取10个热门话题（英文）
    count = 10
    country = "united-states"  # 默认获取美国热门话题（英文）

    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print(f"Invalid count: {sys.argv[1]}, using default 10", file=sys.stderr)

    if len(sys.argv) > 2:
        country = sys.argv[2]

    # 获取热门话题
    trending = fetch_trending_topics(country=country, count=count)

    if not trending:
        print("No trending topics found", file=sys.stderr)
        sys.exit(1)

    # 构建输出数据
    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "xtrends.in",
        "country": country,
        "language": "en",
        "categories": trending
    }

    # 输出JSON
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
