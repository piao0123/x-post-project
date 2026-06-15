#!/usr/bin/env python3
"""
图片下载脚本
优先使用Pexels API，失败时回退到本地库，再失败则使用picsum.photos
"""

import json
import subprocess
import sys
import os
import random
import requests

def get_image_from_pexels(query, output_path):
    """从 Pexels API 获取图片"""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("❌ PEXELS_API_KEY 未设置，跳过 Pexels", file=sys.stderr)
        return False

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            print(f"Pexels API 返回错误 {response.status_code}: {response.text}", file=sys.stderr)
            return False

        data = response.json()
        if not data.get("photos"):
            print("Pexels API 未返回图片", file=sys.stderr)
            return False

        image_url = data["photos"][0]["src"]["original"]
        print(f"✅ 从 Pexels 获取图片: {image_url}")

        # 下载图片
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code != 200:
            print(f"下载图片失败: {img_response.status_code}", file=sys.stderr)
            return False

        with open(output_path, 'wb') as f:
            f.write(img_response.content)
        return True

    except Exception as e:
        print(f"Pexels API 请求异常: {e}", file=sys.stderr)
        return False

def get_image_from_library(category):
    """从本地图片库获取图片"""
    library_path = f"/Users/piaoxian/x-post-project/images/library/{category}"
    if not os.path.exists(library_path):
        print(f"本地图片库目录不存在: {library_path}", file=sys.stderr)
        return None

    images = [f for f in os.listdir(library_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        print(f"本地图片库中无图片: {category}", file=sys.stderr)
        return None

    # 随机选择一张图片
    selected_image = random.choice(images)
    return os.path.join(library_path, selected_image)

def get_image_from_picsum(query, output_path):
    """从 picsum.photos 获取图片作为最后手段"""
    try:
        url = f"https://picsum.photos/800/600?random={hash(query) % 1000}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ 从 picsum.photos 获取图片: {url}")
            return True
        else:
            print(f"picsum.photos 返回 {response.status_code}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"picsum.photos 请求异常: {e}", file=sys.stderr)
        return False

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python3 download-free-image.py <搜索关键词> <输出路径>")
        sys.exit(1)

    query = sys.argv[1]
    output_path = sys.argv[2]

    # 映射关键词到分类
    category_map = {
        "f1": "f1", "formula 1": "f1", "monacogp": "f1", "hamilton": "f1", "verstappen": "f1",
        "ai": "tech", "technology": "tech", "innovation": "tech", "startup": "tech", "gadget": "tech",
        "nba": "sports", "nfl": "sports", "soccer": "sports", "tennis": "sports", "olympics": "sports",
        "startup": "business", "investing": "business", "economy": "business", "market": "business", "finance": "business",
        "space": "science", "nasa": "science", "physics": "science", "climate": "science", "research": "science"
    }

    category = "tech"  # 默认
    for keyword, cat in category_map.items():
        if keyword in query.lower():
            category = cat
            break

    # 优先使用 Pexels API
    if get_image_from_pexels(query, output_path):
        print(f"✅ 图片已通过 Pexels API 下载: {output_path}")
        return

    # 失败则尝试本地库
    local_image = get_image_from_library(category)
    if local_image:
        try:
            import shutil
            shutil.copy2(local_image, output_path)
            print(f"✅ 从本地库获取图片: {output_path}")
            return
        except Exception as e:
            print(f"复制本地图片失败: {e}", file=sys.stderr)

    # 最后手段：picsum.photos
    if get_image_from_picsum(query, output_path):
        print(f"✅ 图片已通过 picsum.photos 下载: {output_path}")
        return

    print(f"❌ 所有图片源均失败", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()