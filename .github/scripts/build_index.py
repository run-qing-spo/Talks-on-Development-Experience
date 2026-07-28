#!/usr/bin/env python3
"""部署时扫描 docs/ 下的文章 HTML，把列表注入 index.html。

仓库中的 docs/index.html 只是模板；本脚本在 CI 里把
<ul class="articles" id="article-list"> ... </ul> 的内容替换为
实际文章列表（按 git 最近提交时间倒序），结果写入输出目录。
"""
import re
import subprocess
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

DOCS = Path("docs")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")


def last_commit_ts(path: Path) -> int:
    out = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    return int(out) if out else 0


articles = [p for p in DOCS.glob("*.html") if p.name != "index.html"]
articles.sort(key=last_commit_ts, reverse=True)

items = "\n".join(
    '    <li><a href="{}">{}</a></li>'.format(quote(p.name), escape(p.stem))
    for p in articles
) or '    <li class="empty">暂无文章</li>'

index = (DOCS / "index.html").read_text(encoding="utf-8")
new_index, n = re.subn(
    r'(<ul class="articles" id="article-list">).*?(</ul>)',
    lambda m: m.group(1) + "\n" + items + "\n  " + m.group(2),
    index,
    flags=re.S,
)
if n != 1:
    sys.exit("error: article-list placeholder not found in docs/index.html")

# 整个 docs 作为站点内容拷贝到输出目录，再覆盖生成好的 index.html
subprocess.run(["rm", "-rf", str(OUT)], check=True)
subprocess.run(["cp", "-R", str(DOCS), str(OUT)], check=True)
(OUT / "index.html").write_text(new_index, encoding="utf-8")
print(f"generated index with {len(articles)} article(s):")
for p in articles:
    print("  -", p.name)
