# -*- coding: utf-8 -*-
"""build_all.py — src/*.src.html  ->  dist/*.html

把 Tailwind Play CDN 换成本地内联块（从 dist/igo-2b.html 里取，已验证可用），
并把 Google Fonts 改成异步加载。

用法：
    python tools/build_all.py              # 全部重建
    python tools/build_all.py cognition    # 只重建 cognition（可多个，不写后缀）
"""
import os, re, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
DIST = os.path.join(REPO, "dist")
HOST_FILE = os.path.join(DIST, "igo-2b.html")

FONT_RE = r'<link href="https://fonts\.googleapis\.com/css2\?[^"]+" rel="stylesheet">'
ASYNC_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700'
    '&family=JetBrains+Mono:wght@400;500;600;700&display=swap" media="print" onload="this.media=\'all\'">'
)

host = open(HOST_FILE, encoding="utf-8").read()
marker = "<!-- Tailwind Play CDN v3 已内联"
start = host.index(marker)
end = host.index("</script>", start) + len("</script>")
inline_block = host[start:end]

targets = sys.argv[1:]
files = sorted(glob.glob(os.path.join(SRC, "*.src.html")))
if targets:
    files = [f for f in files if any(t in os.path.basename(f) for t in targets)]
if not files:
    sys.exit("没有匹配的源文件")

for src_path in files:
    name = os.path.basename(src_path).replace(".src.html", ".html")
    out_path = os.path.join(DIST, name)
    src = open(src_path, encoding="utf-8").read()
    if '<script src="https://cdn.tailwindcss.com"></script>' not in src:
        print("SKIP  %-26s 无 Tailwind CDN 锚点（可能已内联过）" % name)
        continue
    out = src.replace('<script src="https://cdn.tailwindcss.com"></script>', inline_block, 1)
    if re.search(FONT_RE, out):
        out = re.sub(FONT_RE, ASYNC_FONTS, out, count=1)
    else:
        print("WARN  %-26s 未找到 Google Fonts 链接" % name)
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    print("BUILD %-26s %d chars -> dist/%s" % (name, len(out), name))
