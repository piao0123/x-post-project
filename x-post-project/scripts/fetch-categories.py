#!/usr/bin/env python3
"""
X平台固定分区配置
提供科技、娱乐、生活、游戏、音乐5个固定分区
"""

import json
import sys
from datetime import datetime

# 固定的5个大分类
CATEGORIES = [
    {
        "id": "tech",
        "name": "Technology",
        "name_cn": "科技",
        "keywords": ["AI", "tech", "startup", "coding", "programming", "software"],
        "search_query": "AI OR tech OR startup OR software",
        "description": "Artificial Intelligence, Software, Hardware, Startups"
    },
    {
        "id": "entertainment",
        "name": "Entertainment",
        "name_cn": "娱乐",
        "keywords": ["movie", "music", "celebrity", "gaming", "anime"],
        "search_query": "movie OR music OR celebrity OR gaming",
        "description": "Movies, Music, Celebrity, Gaming, Anime"
    },
    {
        "id": "lifestyle",
        "name": "Lifestyle",
        "name_cn": "生活",
        "keywords": ["travel", "food", "health", "fitness", "fashion"],
        "search_query": "travel OR food OR health OR fitness",
        "description": "Travel, Food, Health, Fashion, Wellness"
    },
    {
        "id": "gaming",
        "name": "Gaming",
        "name_cn": "游戏",
        "keywords": ["PS5", "Xbox", "Nintendo", "esports", "streamer"],
        "search_query": "PS5 OR Xbox OR Nintendo OR esports",
        "description": "Console Gaming, PC Gaming, Esports, Streamers"
    },
    {
        "id": "music",
        "name": "Music",
        "name_cn": "音乐",
        "keywords": ["album", "concert", "artist", "Grammy", "Billboard"],
        "search_query": "album OR concert OR artist OR Grammy",
        "description": "Albums, Concerts, Artists, Awards, Charts"
    }
]

def get_categories():
    """获取所有固定分区"""
    return CATEGORIES

def get_category_by_id(category_id):
    """根据ID获取分区"""
    for cat in CATEGORIES:
        if cat["id"] == category_id:
            return cat
    return None

def main():
    """主函数"""
    output = {
        "fetched_at": datetime.now().isoformat(),
        "source": "predefined",
        "language": "en",
        "categories": CATEGORIES
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
