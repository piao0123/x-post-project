#!/usr/bin/env python3
"""
字数检查脚本 - X帖子字符计数工具
检查内容是否符合X平台字数限制（280字符）
"""

import sys
import re
import os


def count_x_characters(text):
    """
    计算X平台实际字符数
    - 普通推文: 280字符
    - Premium用户: 10,000字符
    - URL计为23字符（不含http://或https://前缀，但包含域名和路径）
    - @用户名不计入
    """
    if not text:
        return 0

    # 移除非显示字符但保留换行（换行计为1字符）
    clean_text = text.strip()

    # 提取并替换URL为占位符（URL统一计为23字符）
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, clean_text)
    text_without_urls = re.sub(url_pattern, 'https://x.com/url', clean_text)

    # 移除@用户名（@username不计入）
    text_without_mentions = re.sub(r'@\w+', '', text_without_urls)

    # 计算基础字符数
    base_count = len(text_without_mentions)

    # 每个URL额外加23字符
    url_count = len(urls) * 23

    return base_count + url_count


def format_count(count, limit=280):
    """格式化字符计数显示"""
    percentage = (count / limit) * 100
    status = "✅" if count <= limit else "❌"
    return f"{status} 字符数: {count}/{limit} ({percentage:.1f}%)"


def main():
    # 支持两种输入方式：命令行参数或管道输入
    if len(sys.argv) < 2:
        print("用法: python3 check-char-count.py <文本内容>")
        print("   或: python3 check-char-count.py <filepath>")
        print("   或: echo '文本内容' | python3 check-char-count.py")
        print("")
        print("示例:")
        print('  python3 check-char-count.py "这是测试内容"')
        print('  python3 check-char-count.py post.md')
        print('  echo "Hello world" | python3 check-char-count.py')
        sys.exit(1)

    if sys.argv[1] == '-':
        # 从stdin读取
        text = sys.stdin.read().strip()
    elif os.path.isfile(sys.argv[1]):
        # 文件路径参数
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if file_path.endswith('.md'):
                    # 移除markdown标题
                    text = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
                    # 移除链接但保留文字
                    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
                    # 移除图片
                    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
                    # 移除代码块
                    text = re.sub(r'```[\s\S]*?```', '', text)
                    # 移除行内代码
                    text = re.sub(r'`[^`]+`', '', text)
                else:
                    text = content
        except Exception as e:
            print(f"错误: 读取文件失败 - {e}")
            sys.exit(1)
    else:
        # 命令行文本参数（所有剩余参数拼接）
        text = ' '.join(sys.argv[1:])

    count = count_x_characters(text)

    print(f"\n{'='*50}")
    print(f"X帖子字数检查")
    print(f"{'='*50}")
    print(f"内容预览: {text[:100]}{'...' if len(text) > 100 else ''}")
    print(f"原始长度: {len(text)}字符")
    print(f"X实际字符数: {count}（已扣除@用户名，URL计23字符）")
    print()
    print(format_count(count))
    print()

    if count > 280:
        print("⚠️  内容超过280字符限制")
        print("建议: 精简内容或使用Thread（推文串）")
        return 1
    elif count > 260:
        print("💡 提示: 接近字符限制，留意URL会占用23字符")
    else:
        print("✅ 内容符合限制，可以发布")

    return 0


if __name__ == "__main__":
    sys.exit(main())