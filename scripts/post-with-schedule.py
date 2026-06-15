#!/usr/bin/env python3
"""
X Post Scheduler - Linux/跨平台版
使用Playwright自动化Chrome，发帖并设置定时

依赖:
    pip3 install playwright
    playwright install chromium
    apt install chromium-browser  # Linux需要

用法:
    python3 post-with-schedule.py <content_file> [image_file] [--schedule "YYYY-MM-DD HH:MM"]
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误: 需要安装playwright")
    print("运行: pip3 install playwright && playwright install chromium")
    sys.exit(1)


# ── 颜色输出 ──────────────────────────────────────────
def info(msg):
    print(f"\033[0;32m[INFO]\033[0m {msg}")

def warn(msg):
    print(f"\033[1;33m[WARN]\033[0m {msg}")

def error(msg):
    print(f"\033[0;31m[ERROR]\033[0m {msg}")


# ── 命令行参数解析 ────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="X帖子定时发布工具 (Linux版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 post-with-schedule.py post.txt                    # 立即发布纯文字
  python3 post-with-schedule.py post.txt image.jpg          # 立即发布带图
  python3 post-with-schedule.py post.txt --schedule "2026-06-15 21:00"  # 定时发布
  python3 post-with-schedule.py post.txt image.jpg --schedule "2026-06-16 20:00"
        """
    )
    parser.add_argument('content_file', help='帖子内容文件路径（纯文字）')
    parser.add_argument('image_file', nargs='?', default=None, help='图片文件路径（可选）')
    parser.add_argument('--schedule', dest='schedule_time',
                        help='定时时间，格式: YYYY-MM-DD HH:MM')
    parser.add_argument('--headless', action='store_true',
                        help='无头模式（不显示浏览器窗口）')
    parser.add_argument('--timeout', type=int, default=30000,
                        help='页面操作超时时间(ms)，默认30000')
    parser.add_argument('--chrome-path', dest='chrome_path', default=None,
                        help='Chrome/Chromium可执行文件路径')

    args = parser.parse_args()

    # 验证文件存在
    if not os.path.isfile(args.content_file):
        error(f"内容文件不存在: {args.content_file}")
        sys.exit(1)

    if args.image_file and not os.path.isfile(args.image_file):
        error(f"图片文件不存在: {args.image_file}")
        sys.exit(1)

    return args


# ── 日期时间解析 ─────────────────────────────────────
def parse_schedule_time(time_str):
    """
    解析 YYYY-MM-DD HH:MM 格式
    不strip前导零！X的select value可能是 "05" 而不是 "5"
    """
    try:
        date_part, time_part = time_str.strip().split(' ')
        year, month, day = date_part.split('-')
        hour, minute = time_part.split(':')
        return {
            'year': year,
            'month': month,   # 保持原样，不strip
            'day': day,
            'hour': hour,
            'minute': minute,
        }
    except ValueError:
        error(f"时间格式错误: {time_str}，期望: YYYY-MM-DD HH:MM")
        sys.exit(1)


# ── 核心发布逻辑 ─────────────────────────────────────
async def post_to_x(content_file, image_file, schedule_time, headless, timeout, chrome_path):
    info("=== X Post Scheduler (Linux版) ===")

    # 读取内容
    with open(content_file, 'r', encoding='utf-8') as f:
        post_text = f.read().strip()

    if not post_text:
        error("帖子内容为空")
        return False

    info(f"内容长度: {len(post_text)} 字符")

    # 解析定时时间
    schedule_info = None
    if schedule_time:
        schedule_info = parse_schedule_time(schedule_time)
        info(f"定时时间: {schedule_info['year']}-{schedule_info['month']}-{schedule_info['day']} "
             f"{schedule_info['hour']}:{schedule_info['minute']}")

    info(f"图片: {image_file or '无'}")

    # 启动Playwright
    async with async_playwright() as p:
        # 启动Chromium
        browser_kwargs = {
            'headless': headless,
        }
        if chrome_path:
            browser_kwargs['executable_path'] = chrome_path
        else:
            # 尝试自动找Chrome
            possible_paths = [
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/usr/bin/google-chrome',
                '/snap/bin/chromium',
            ]
            for path in possible_paths:
                if os.path.isfile(path):
                    browser_kwargs['executable_path'] = path
                    info(f"使用Chrome: {path}")
                    break

        browser = await p.chromium.launch(**browser_kwargs)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 创建新标签页打开发帖页面
        page = await context.new_page()
        info("[1/7] 打开发帖页面...")
        await page.goto('https://x.com/compose/post', wait_until='domcontentloaded', timeout=timeout)
        await page.wait_for_timeout(3000)  # 等待React渲染

        # Step 2: 粘贴文字到编辑器
        info("[2/7] 粘贴文字...")

        # 尝试多种选择器找编辑器
        editor = None
        selectors = [
            'div[role="textbox"]',
            'div[data-testid="tweetTextarea_0"]',
            'div[contenteditable="true"][role="textbox"]',
            'div[aria-label*="Post"]',
        ]
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    editor = el
                    info(f"  找到编辑器: {sel}")
                    break
            except Exception:
                pass

        if not editor:
            error("无法找到发帖编辑器")
            await browser.close()
            return False

        # 点击编辑器获取焦点
        await editor.click()
        await page.wait_for_timeout(500)

        # 粘贴文字
        await page.keyboard.type(post_text, delay=10)
        info("  文字粘贴完成")
        await page.wait_for_timeout(1000)

        # Step 3: 上传图片（如果有）
        # ⚠️ 关键：X平台需要先点击Media按钮才会出现input[type=file]
        # 不能直接找input，必须先点击按钮
        if image_file:
            info("[3/7] 上传图片...")
            try:
                # 3a: 先找并点击Media按钮，让input[type=file]出现
                media_clicked = False
                media_selectors = [
                    'button[aria-label*="Media" i]',
                    'button[aria-label*="Add media" i]',
                    '[data-testid="addImageButton"]',
                    '[data-testid="fileInput"]',
                    'button:has-text("Media")',
                    'button:has-text("Add images")',
                    'svg[data-testid="addImageIcon"]',
                    'div[aria-label*="Add photos" i]',
                ]
                for sel in media_selectors:
                    try:
                        media_btn = await page.query_selector(sel)
                        if media_btn and await media_btn.is_visible():
                            await media_btn.click()
                            media_clicked = True
                            info(f"  Media按钮已点击: {sel}")
                            await page.wait_for_timeout(1500)  # 等待UI更新
                            break
                    except Exception:
                        pass

                if not media_clicked:
                    warn("  未找到Media按钮，尝试直接找文件input")

                # 3b: 现在找文件上传input并上传
                file_input = None
                for sel in ['input[type="file"]', '[data-testid="fileInput"] input']:
                    try:
                        fi = await page.query_selector(sel)
                        if fi and await fi.is_visible():
                            file_input = fi
                            info(f"  找到文件input: {sel}")
                            break
                    except Exception:
                        pass

                if file_input:
                    await file_input.set_input_files(image_file)
                    info(f"  图片已选择: {os.path.basename(image_file)}")
                    await page.wait_for_timeout(4000)  # 等待图片上传 + 预览渲染
                else:
                    warn("  无法找到文件上传input，图片上传失败")
                    warn("  请手动: 点击Media → 选择图片 → 继续")
            except Exception as e:
                warn(f"  图片上传失败: {e}")
                warn("  请手动完成图片上传")
        else:
            info("[3/7] 无图片，跳过")


        # Step 4: 点击Schedule按钮（如果设置了定时）
        if schedule_info:
            info("[4/7] 点击Schedule post...")
        else:
            info("[4/7] 点击Post（立即发布）...")

        try:
            schedule_btn = None
            for sel in [
                'button:has-text("Schedule post")',
                'button:has-text("Schedule")',
                '[data-testid="schedulePost"]',
                'button[role="button"]:has-text("Schedule")',
            ]:
                try:
                    btn = await page.query_selector(sel)
                    if btn:
                        schedule_btn = btn
                        break
                except Exception:
                    pass

            if schedule_btn:
                await schedule_btn.click()
                info("  Schedule按钮已点击")
                await page.wait_for_timeout(2000)
            else:
                warn("  未找到Schedule按钮，请手动点击")
        except Exception as e:
            warn(f"  点击Schedule按钮失败: {e}")

        # Step 5: 设置定时日期时间
        if schedule_info:
            info("[5/7] 设置定时时间...")

            try:
                # 等待日期选择器出现
                await page.wait_for_timeout(2000)

                # 尝试JavaScript方式直接设置select值
                result = await page.evaluate("""
                    () => {
                        const selects = document.querySelectorAll('select');
                        if (selects.length === 0) return { success: false, msg: 'No selects found' };

                        const data = {
                            success: true,
                            selects: selects.length,
                            options: []
                        };

                        selects.forEach((sel, i) => {
                            const opts = Array.from(sel.options).map(o => ({
                                value: o.value,
                                text: o.text
                            }));
                            data.options.push({ index: i, opts });
                        });

                        return data;
                    }
                """)
                info(f"  找到 {result.get('selects', 0)} 个选择器")

                if result.get('success') and result.get('selects', 0) >= 5:
                    # 设置月份
                    await page.evaluate("""
                        () => {
                            const selects = document.querySelectorAll('select');
                            // 常见顺序: 月, 日, 年, 时, 分
                            // X的select value可能是 "05"（带前导零）
                            const month = arguments[0];
                            const day = arguments[1];
                            const year = arguments[2];
                            const hour = arguments[3];
                            const minute = arguments[4];

                            // 尝试直接设值
                            selects[0].value = month;
                            selects[0].dispatchEvent(new Event('change', {bubbles: true}));
                            selects[1].value = day;
                            selects[1].dispatchEvent(new Event('change', {bubbles: true}));
                            selects[2].value = year;
                            selects[2].dispatchEvent(new Event('change', {bubbles: true}));
                            selects[3].value = hour;
                            selects[3].dispatchEvent(new Event('change', {bubbles: true}));
                            selects[4].value = minute;
                            selects[4].dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    """, schedule_info['month'], schedule_info['day'], schedule_info['year'],
                        schedule_info['hour'], schedule_info['minute'])

                    info(f"  已设置: {schedule_info['month']}/{schedule_info['day']}/"
                         f"{schedule_info['year']} {schedule_info['hour']}:{schedule_info['minute']}")
                    await page.wait_for_timeout(1000)

                    # 点击Confirm
                    info("  点击Confirm...")
                    confirm_btn = None
                    for sel in [
                        'button:has-text("Confirm")',
                        'button:has-text("confirm")',
                        '[role="button"]:has-text("Confirm")',
                    ]:
                        try:
                            btn = await page.query_selector(sel)
                            if btn:
                                confirm_btn = btn
                                break
                        except Exception:
                            pass

                    if confirm_btn:
                        await confirm_btn.click()
                        info("  Confirm已点击")
                        await page.wait_for_timeout(1000)
                    else:
                        warn("  未找到Confirm按钮，请手动确认时间")
                else:
                    warn("  日期选择器未就绪，请手动设置时间")

            except Exception as e:
                warn(f"  设置时间失败: {e}")

        # Step 6: 验证和用户确认
        info("[6/7] 验证...")
        try:
            page_text = await page.evaluate("() => document.body.innerText.substring(0, 800)")
            info(f"  页面内容预览:\n{page_text[:300]}...")
        except Exception as e:
            warn(f"  获取页面内容失败: {e}")

        # Step 7: 等待用户手动确认
        info("[7/7] 等待用户确认...")
        print()
        info("=" * 50)
        if schedule_info:
            info(f"✅ 定时已设置: {schedule_info['year']}-{schedule_info['month']}-{schedule_info['day']} "
                 f"{schedule_info['hour']}:{schedule_info['minute']}")
        info("请在浏览器中检查并手动点击【Schedule】或【Post】按钮完成发布")
        info("按 Enter 关闭浏览器...")
        info("=" * 50)
        print()

        # 等待用户按Enter
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

        await browser.close()
        info("浏览器已关闭")

    return True


# ── 主入口 ───────────────────────────────────────────
def main():
    args = parse_args()

    if args.schedule_time:
        parse_schedule_time(args.schedule_time)  # 提前验证格式

    try:
        success = asyncio.run(
            post_to_x(
                content_file=args.content_file,
                image_file=args.image_file,
                schedule_time=args.schedule_time,
                headless=args.headless,
                timeout=args.timeout,
                chrome_path=args.chrome_path,
            )
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        info("操作已取消")
        sys.exit(130)
    except Exception as e:
        error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()