#!/usr/bin/env python3
"""
从Pexels API搜索并下载图片
"""

import json
import os
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import urlencode

def search_images(keyword, api_key, count=5):
    """
    从Pexels API搜索图片

    Args:
        keyword: 搜索关键词
        api_key: Pexels API Key
        count: 返回的图片数量

    Returns:
        list: 图片信息列表
    """
    url = "https://api.pexels.com/v1/search"
    params = {
        "query": keyword,
        "per_page": count,
        "orientation": "landscape"  # 横版图片更适合X帖子
    }

    try:
        # 设置请求头
        headers = {
            "Authorization": api_key
        }

        # 构建完整URL
        full_url = f"{url}?{urlencode(params)}"
        req = Request(full_url, headers=headers)

        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        # 提取图片信息
        images = []
        for photo in data.get('photos', []):
            image = {
                'id': photo.get('id'),
                'url': photo.get('src', {}).get('large'),
                'width': photo.get('width'),
                'height': photo.get('height'),
                'photographer': photo.get('photographer'),
                'photographer_url': photo.get('photographer_url'),
                'alt': photo.get('alt', '')
            }
            images.append(image)

        return images

    except Exception as e:
        print(f"Error searching images: {e}", file=sys.stderr)
        return []

def download_image(url, output_path):
    """
    下载图片到指定路径

    Args:
        url: 图片URL
        output_path: 输出文件路径

    Returns:
        bool: 是否下载成功
    """
    try:
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        req = Request(url, headers=headers)

        with urlopen(req, timeout=60) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())

        return True

    except Exception as e:
        print(f"Error downloading image: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: fetch-image.py <keyword> <output_path> [api_key]", file=sys.stderr)
        print("Set PEXELS_API_KEY environment variable or pass as third argument", file=sys.stderr)
        sys.exit(1)

    keyword = sys.argv[1]
    output_path = sys.argv[2]

    # 获取API Key
    api_key = os.environ.get('PEXELS_API_KEY')
    if len(sys.argv) > 3:
        api_key = sys.argv[3]

    if not api_key:
        print("Error: Pexels API Key required", file=sys.stderr)
        print("Set PEXELS_API_KEY environment variable or pass as third argument", file=sys.stderr)
        sys.exit(1)

    # 搜索图片
    print(f"Searching for images with keyword: {keyword}", file=sys.stderr)
    images = search_images(keyword, api_key, count=5)

    if not images:
        print("No images found", file=sys.stderr)
        sys.exit(1)

    # 选择第一张图片下载
    image = images[0]
    print(f"Downloading image from: {image['url']}", file=sys.stderr)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 下载图片
    if download_image(image['url'], output_path):
        print(f"Image downloaded to: {output_path}", file=sys.stderr)

        # 输出图片信息
        output = {
            "fetched_at": datetime.now().isoformat(),
            "keyword": keyword,
            "image": {
                "path": output_path,
                "url": image['url'],
                "width": image['width'],
                "height": image['height'],
                "photographer": image['photographer'],
                "photographer_url": image['photographer_url'],
                "alt": image['alt']
            }
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("Failed to download image", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
