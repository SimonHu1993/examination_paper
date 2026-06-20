#!/usr/bin/env python3
"""将 questions.json 内嵌到 index.html 中，生成可本地直接打开的独立文件"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# 读取 JSON 数据
with open(os.path.join(BASE, 'questions.json'), 'r', encoding='utf-8') as f:
    json_data = f.read().strip()

# 读取 HTML
with open(os.path.join(BASE, 'index.html'), 'r', encoding='utf-8') as f:
    html = f.read()

# 在 </head> 前插入内嵌数据
embedded = f'    <script type="application/json" id="embeddedQuizData">\n{json_data}\n    </script>\n'
html_out = html.replace('</head>', embedded + '</head>')

# 输出
out_path = os.path.join(BASE, 'index_local.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_out)

print(f'Done! {out_path} ({len(html_out)} bytes)')
print(f'JSON: {len(json_data)} chars, HTML: {len(html)} chars')
