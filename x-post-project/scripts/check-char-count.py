#!/usr/bin/env python3
"""
X平台字数检查工具（优化版）
考虑X平台的实际字符计数规则
"""

import re
import sys
from urllib.parse import urlparse

def count_chars_twitter(text):
    """
    计算X平台的字符数（考虑URL缩短等规则）

    X平台规则：
    1. 所有字符都计为1
    2. URL统一计为23个字符（使用t.co缩短）
    3. @用户名不计入字符数
    4. #话题标签计入字符数

    Args:
        text: 要计算的文本

    Returns:
        int: 字符数
    """
    # 移除@用户名（不计入字符数）
    text_without_mentions = re.sub(r'@\w+', '', text)

    # 计算URL数量并替换为23个字符
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text_without_mentions)
    text_without_urls = re.sub(url_pattern, 'x' * 23, text_without_mentions)

    # 计算字符数
    char_count = len(text_without_urls)

    return char_count

def check_char_limit(text, is_premium=False):
    """
    检查字符数是否符合限制

    Args:
        text: 要检查的文本
        is_premium: 是否为Premium用户

    Returns:
        tuple: (字符数, 限制, 是否符合)
    """
    char_count = count_chars_twitter(text)
    limit = 10000 if is_premium else 280

    return char_count, limit, char_count <= limit

def extract_content_from_markdown(md_text):
    """
    从Markdown文件中提取纯文本内容

    Args:
        md_text: Markdown文本

    Returns:
        str: 纯文本内容
    """
    # 移除Markdown格式
    # 移除标题
    text = re.sub(r'^#+\s+.*$', '', md_text, flags=re.MULTILINE)
    # 移除粗体和斜体
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    # 移除链接格式，保留URL
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\2', text)
    # 移除图片格式
    text = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', '', text)
    # 移除代码块
    text = re.sub(r'`[^`]+`', '', text)
    # 移除多余空行
    text = re.sub(r'\n\s*\n', '\n', text)
    # 移除首尾空格
    text = text.strip()

    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: check-char-count.py <file_path> [--premium]", file=sys.stderr)
        print("Options:", file=sys.stderr)
        print("  --premium  检查Premium用户限制(10000字符)", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    is_premium = '--premium' in sys.argv

    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 如果是Markdown文件，提取纯文本
        if file_path.endswith('.md'):
            content = extract_content_from_markdown(content)

        # 检查字符数
        char_count, limit, is_valid = check_char_limit(content, is_premium)

        # 输出结果
        result = {
            "file": file_path,
            "char_count": char_count,
            "limit": limit,
            "is_premium": is_premium,
            "is_valid": is_valid,
            "remaining": limit - char_count
        }

        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 如果不符合限制，返回错误码
        if not is_valid:
            sys.exit(1)

    except FileNotFoundError:
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import json
    main()
