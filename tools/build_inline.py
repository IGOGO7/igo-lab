#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通用：<name>.src.html -> <name>.html
把 Tailwind Play CDN 换成本地已验证的内联块（取自 igo-2b.html），
Google Fonts 改异步加载。用法：python _build_inline.py <input.src.html> [output.html]"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
src_path = sys.argv[1] if len(sys.argv) > 1 else None
if not src_path:
    print("usage: python _build_inline.py <input.src.html> [output.html]"); sys.exit(1)
if not os.path.isabs(src_path):
    src_path = os.path.join(HERE, src_path)
out_path = sys.argv[2] if len(sys.argv) > 2 else src_path.replace('.src.html', '.html')

host = open(os.path.join(HERE, 'igo-2b.html'), encoding='utf-8').read()
marker = '<!-- Tailwind Play CDN v3 已内联'
start = host.index(marker)
end = host.index('</script>', start) + len('</script>')
inline_block = host[start:end]

src = open(src_path, encoding='utf-8').read()
assert '<script src="https://cdn.tailwindcss.com"></script>' in src, 'Tailwind CDN 锚点缺失'
out = src.replace('<script src="https://cdn.tailwindcss.com"></script>', inline_block, 1)

font_re = r'<link href="https://fonts\.googleapis\.com/css2\?[^"]+" rel="stylesheet">'
if re.search(font_re, out):
    out = re.sub(font_re,
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" media="print" onload="this.media=\'all\'">',
        out, count=1)
else:
    print('WARN: 未找到 Google Fonts 链接，跳过字体异步化')

open(out_path, 'w', encoding='utf-8', newline='').write(out)
print(os.path.basename(out_path), ':', len(out), 'chars; inline tailwind:', len(inline_block))

scripts = re.findall(r'<script>([\s\S]*?)</script>', out)
main_js = scripts[-1]
chk = os.path.join(HERE, '_' + os.path.basename(out_path).replace('.html', '') + '_check.js')
open(chk, 'w', encoding='utf-8', newline='').write(main_js)
print('main js ->', os.path.basename(chk), len(main_js), 'chars')
