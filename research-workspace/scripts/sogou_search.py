#!/usr/bin/env python3
"""搜狗搜索脚本 - 简化实现版"""

import sys, json, re
from argparse import ArgumentParser

def search(query, pages=1, json_output=False):
    """执行搜狗搜索"""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        # 尝试虚拟环境
        import subprocess
        sys.exit(subprocess.call([PYBIN, __file__] + sys.argv[1:]))

    results = []
    for page in range(pages):
        offset = page * 10
        url = f"https://www.sogou.com/web?query={query}&start={offset}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for item in soup.select(".vrwrap, .rb")[:10]:
            title_elem = item.select_one("h3 a, .vr-title a") or item.find("a")
            snippet_elem = item.select_one(".space-txt, .str_info, .abstract")
            if title_elem:
                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet})
        
        import time
        time.sleep(1.5)
    
    if json_output:
        print(json.dumps({"query": query, "total_results": len(results), "results": results}, ensure_ascii=False, indent=2))
    else:
        print(f"搜索关键词: {query}")
        print(f"结果数量: {len(results)} 条（共 {pages} 页）")
        print("=" * 60)
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r['title']}")
            print(f"    链接: {r['url']}")
            print(f"    摘要: {r['snippet'][:120]}")
    
    return results

def fetch(url, max_chars=15000):
    """抓取网页正文"""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        import subprocess
        sys.exit(subprocess.call([PYBIN, __file__, "fetch"] + [url]))
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 去除脚本和样式
    for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    print(text[:max_chars])

if __name__ == "__main__":
    PYBIN = "/app/custom/.venv-container/bin/python3"
    parser = ArgumentParser(description="搜狗搜索脚本")
    sub = parser.add_subparsers(dest="cmd")
    
    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--pages", type=int, default=1)
    p_search.add_argument("--json", action="store_true")
    
    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("url")
    p_fetch.add_argument("--max-chars", type=int, default=15000)
    
    args = parser.parse_args()
    
    if args.cmd == "search":
        search(args.query, args.pages, args.json)
    elif args.cmd == "fetch":
        fetch(args.url, args.max_chars)
    else:
        parser.print_help()
