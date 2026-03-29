#!/usr/bin/env python3
"""
搜狗搜索爬虫 — 为投研深度搜索提供检索能力。

功能：
  search  - 搜索关键词，返回结构化结果列表（标题、URL、摘要）
  fetch   - 抓取指定 URL 的正文内容（自动提取可读文本）

用法：
  python scripts/sogou_search.py search "关键词" [--pages 3] [--json]
  python scripts/sogou_search.py fetch "https://example.com/article"
"""

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
from dataclasses import asdict, dataclass, field
from typing import List, Optional

try:
    import requests
except ImportError:
    print("Error: requests 未安装，请执行: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 未安装，请执行: pip install beautifulsoup4", file=sys.stderr)
    sys.exit(1)


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]


@dataclass
class SearchResult:
    """单条搜索结果"""
    rank: int
    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class SearchResponse:
    """搜索响应"""
    query: str
    total_results: int
    page_count: int
    results: List[SearchResult] = field(default_factory=list)


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return session


def _resolve_sogou_redirect(session: requests.Session, sogou_url: str) -> str:
    """解析搜狗的重定向链接，获取真实 URL。

    搜狗使用 JS window.location.replace() 跳转而非 HTTP 302，
    因此需要 GET 页面内容并用正则提取目标 URL。
    """
    if not sogou_url:
        return sogou_url
    if sogou_url.startswith("/link"):
        sogou_url = "https://www.sogou.com" + sogou_url
    if "sogou.com/link" not in sogou_url:
        return sogou_url
    try:
        resp = session.get(sogou_url, allow_redirects=True, timeout=8)
        match = re.search(
            r'window\.location\.replace\(["\'](.+?)["\']\)',
            resp.text,
        )
        if match:
            return match.group(1)
        match = re.search(r"content=[\"']0;URL='(.+?)'", resp.text)
        if match:
            return match.group(1)
        return sogou_url
    except Exception:
        return sogou_url


def _extract_source_domain(url: str) -> str:
    """从 URL 中提取域名作为来源标识。"""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def search(query: str, pages: int = 1, resolve_urls: bool = True) -> SearchResponse:
    """
    执行搜狗搜索，返回结构化结果。

    Args:
        query: 搜索关键词
        pages: 搜索页数（每页约 10 条结果）
        resolve_urls: 是否解析搜狗重定向链接为真实 URL
    """
    session = _get_session()
    all_results: List[SearchResult] = []
    rank_offset = 0

    for page in range(1, pages + 1):
        url = "https://www.sogou.com/web"
        params = {"query": query, "page": page, "ie": "utf-8"}

        try:
            resp = session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
        except requests.RequestException as e:
            print(f"[WARN] 第 {page} 页请求失败: {e}", file=sys.stderr)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        result_items = soup.select("div.vrwrap, div.rb")

        if not result_items:
            result_items = soup.select("[class*='result'], [class*='vrwrap']")

        for item in result_items:
            rank_offset += 1

            title_tag = item.select_one("h3 a, .vr-title a, .pt a")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")

            snippet_tag = item.select_one(
                "div.space-txt, p.str-text, div.str-text, "
                "p[class*='text'], div[class*='content'], .star-wiki"
            )
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            if resolve_urls and href:
                href = _resolve_sogou_redirect(session, href)

            source = _extract_source_domain(href)

            all_results.append(SearchResult(
                rank=rank_offset,
                title=title,
                url=href,
                snippet=snippet,
                source=source,
            ))

        if page < pages:
            time.sleep(random.uniform(1.0, 2.5))

    return SearchResponse(
        query=query,
        total_results=len(all_results),
        page_count=pages,
        results=all_results,
    )


def fetch_url_content(url: str, max_chars: int = 15000) -> str:
    """
    抓取指定 URL 的页面正文内容。

    自动去除导航、广告等非正文区域，提取可读文本。

    Args:
        url: 目标页面 URL
        max_chars: 最大返回字符数（防止输出过长）
    """
    session = _get_session()

    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
        if resp.encoding and resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding
    except requests.RequestException as e:
        return f"[ERROR] 无法访问 {url}: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "iframe", "noscript", "form", "button", "svg", "img"]):
        tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    article = (
        soup.find("article")
        or soup.find("div", class_=re.compile(r"(article|content|post|entry|main)", re.I))
        or soup.find("div", id=re.compile(r"(article|content|post|entry|main)", re.I))
    )

    target = article if article else soup.body if soup.body else soup

    paragraphs = []
    for elem in target.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote", "pre", "td"]):
        text = elem.get_text(strip=True)
        if len(text) > 10:
            tag_name = elem.name
            if tag_name in ("h1", "h2", "h3", "h4"):
                text = f"\n## {text}\n"
            elif tag_name == "li":
                text = f"- {text}"
            elif tag_name == "blockquote":
                text = f"> {text}"
            paragraphs.append(text)

    content = "\n".join(paragraphs)

    if not content.strip():
        content = target.get_text(separator="\n", strip=True)

    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n[...内容截断，共 {len(content)} 字符，已显示前 {max_chars} 字符]"

    header = f"# {title}\n来源: {url}\n---\n\n" if title else f"来源: {url}\n---\n\n"
    return header + content


def _format_results_text(response: SearchResponse) -> str:
    """将搜索结果格式化为可读文本。"""
    lines = [
        f"搜索关键词: {response.query}",
        f"结果数量: {response.total_results} 条（共 {response.page_count} 页）",
        "=" * 60,
    ]

    for r in response.results:
        lines.append(f"\n[{r.rank}] {r.title}")
        lines.append(f"    来源: {r.source}")
        lines.append(f"    链接: {r.url}")
        if r.snippet:
            lines.append(f"    摘要: {r.snippet}")
        lines.append("-" * 60)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="搜狗搜索爬虫 — 投研信息检索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # search 子命令
    search_parser = subparsers.add_parser("search", help="搜索关键词")
    search_parser.add_argument("query", help="搜索关键词")
    search_parser.add_argument("--pages", type=int, default=1, help="搜索页数（默认 1）")
    search_parser.add_argument("--json", action="store_true", dest="output_json", help="以 JSON 格式输出")
    search_parser.add_argument("--no-resolve", action="store_true", help="不解析搜狗重定向链接（更快）")

    # fetch 子命令
    fetch_parser = subparsers.add_parser("fetch", help="抓取 URL 正文内容")
    fetch_parser.add_argument("url", help="目标 URL")
    fetch_parser.add_argument("--max-chars", type=int, default=15000, help="最大返回字符数（默认 15000）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "search":
        response = search(
            query=args.query,
            pages=args.pages,
            resolve_urls=not args.no_resolve,
        )
        if args.output_json:
            print(json.dumps(asdict(response), ensure_ascii=False, indent=2))
        else:
            print(_format_results_text(response))

    elif args.command == "fetch":
        content = fetch_url_content(args.url, max_chars=args.max_chars)
        print(content)


if __name__ == "__main__":
    main()
