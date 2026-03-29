#!/usr/bin/env /app/custom/.venv-container/bin/python3
"""
搜狗搜索脚本 - search-for-research 技能核心工具
支持 search (搜索) 和 fetch (抓取正文) 两个命令
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("依赖缺失，请先安装：pip install requests beautifulsoup4", file=sys.stderr)
    sys.exit(1)

DEFAULT_DELAY = (1.0, 2.5)  # 随机延迟范围（秒）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}


def sogou_search(query, pages=1, resolve=True, delay=None):
    """执行搜狗搜索并返回结构化结果"""
    if delay is None:
        delay = DEFAULT_DELAY
    results = []

    for page in range(1, pages + 1):
        offset = (page - 1) * 10
        url = f"https://www.sogou.com/web?query={urllib.parse.quote(query)}&offset={offset}"

        time.sleep(random.uniform(*delay))

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"请求失败 (页{page}): {e}", file=sys.stderr)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # 搜狗搜索结果结构
        for item in soup.select("div.vrwrap, div.rb"):
            try:
                title_tag = item.select_one("h3 a, a.vr-title")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")

                # 解析真实URL（搜狗重定向）
                if resolve and "sogou" in href:
                    try:
                        r = requests.head(href, headers=HEADERS, timeout=5, allow_redirects=True)
                        real_url = r.url
                    except:
                        real_url = href
                else:
                    real_url = href

                # 摘要
                snippet_tag = item.select_one("div.str-text, div.vr-summary, p.str_info")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                # 来源域名
                source = ""
                if real_url:
                    parsed = urllib.parse.urlparse(real_url)
                    source = parsed.netloc

                if title and real_url:
                    results.append({
                        "rank": len(results) + 1,
                        "title": title,
                        "url": real_url,
                        "snippet": snippet[:300] if snippet else "",
                        "source": source,
                    })
            except Exception:
                continue

        # 如果页面没有结果（可能是反爬），尝试备选解析
        if not results:
            for item in soup.select("div.pt战国7, div.results"):
                # 备选：直接解析所有链接
                pass

    return results


def fetch_content(url, max_chars=15000, delay=None):
    """抓取URL的可读正文内容"""
    if delay is None:
        delay = DEFAULT_DELAY

    time.sleep(random.uniform(*delay))

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"请求失败: {e}"}

    # 判断是否搜狗重定向页
    if "sogou" in url:
        soup = BeautifulSoup(resp.text, "html.parser")
        # 提取重定向目标
        redirect = soup.select_one("meta[http-equiv='refresh']")
        if redirect:
            match = re.search(r"url=([^'\"]+)", redirect.get("content", ""))
            if match:
                url = match.group(1)
                try:
                    resp = requests.get(url, headers=HEADERS, timeout=15)
                    resp.raise_for_status()
                except Exception as e:
                    return {"error": f"重定向请求失败: {e}"}

    # 尝试多种编码
    for enc in ("utf-8", "gbk", "gb2312", "gb18030"):
        try:
            resp.encoding = enc
            break
        except:
            continue

    soup = BeautifulSoup(resp.text, "html.parser")

    # 去除脚本、样式、广告等非正文元素
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # 尝试找正文区域
    article = (
        soup.select_one("article") or
        soup.select_one("main") or
        soup.select_one(".article-content") or
        soup.select_one(".content") or
        soup.select_one("#content") or
        soup.select_one("body")
    )

    if article:
        text = article.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # 清理多余空行
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    text = "\n".join(lines)

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... (内容已截断至前 {max_chars} 字符)"

    return {
        "url": url,
        "text": text,
        "length": len(text),
    }


def cmd_search(args):
    """处理 search 命令"""
    results = sogou_search(
        query=args.query,
        pages=args.pages,
        resolve=not args.no_resolve,
        delay=(0.5, 1.5) if args.no_resolve else DEFAULT_DELAY,
    )

    if args.json:
        output = {
            "query": args.query,
            "total_results": len(results),
            "page_count": args.pages,
            "results": results,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"搜索关键词: {args.query}")
        print(f"结果数量: {len(results)} 条（共 {args.pages} 页）")
        print("=" * 60)
        for r in results:
            print(f"\n[{r['rank']}] {r['title']}")
            print(f"来源: {r['source']}")
            print(f"链接: {r['url']}")
            if r["snippet"]:
                print(f"摘要: {r['snippet'][:200]}")
            print("-" * 60)

    return 0


def cmd_fetch(args):
    """处理 fetch 命令"""
    result = fetch_content(args.url, max_chars=args.max_chars)

    if "error" in result:
        print(f"错误: {result['error']}", file=sys.stderr)
        return 1

    print(f"来源: {result['url']}")
    print(f"字数: {result['length']}")
    print("=" * 60)
    print(result["text"])

    return 0


def main():
    parser = argparse.ArgumentParser(description="搜狗搜索脚本 - search-for-research 技能核心工具")
    sub = parser.add_subparsers(dest="command", required=True)

    # search 子命令
    sp = sub.add_parser("search", help="关键词搜索")
    sp.add_argument("query", help="搜索关键词")
    sp.add_argument("--pages", type=int, default=1, help="搜索页数（默认1页，约10条结果）")
    sp.add_argument("--json", action="store_true", help="JSON格式输出")
    sp.add_argument("--no-resolve", action="store_true", help="跳过重定向解析，提升速度")

    # fetch 子命令
    fp = sub.add_parser("fetch", help="抓取URL正文")
    fp.add_argument("url", help="目标URL")
    fp.add_argument("--max-chars", type=int, default=15000, help="限制返回正文字符数（默认15000）")

    args = parser.parse_args()

    if args.command == "search":
        return cmd_search(args)
    elif args.command == "fetch":
        return cmd_fetch(args)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
