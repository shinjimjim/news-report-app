import os
import re

def generate_history_index(history_dir, output_path):
    files = sorted(os.listdir(history_dir), reverse=True)

    # news_YYYY-MM-DD.html 形式にマッチするものだけ
    date_files = [
        f for f in files
        if re.match(r'news_\d{4}-\d{2}-\d{2}\.html$', f)
    ]

    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>過去のニュース一覧</title>
    <style>
        body { font-family: sans-serif; padding: 2rem; max-width: 800px; margin: auto; }
        h1 { font-size: 1.6rem; }
        ul { padding-left: 1.2rem; }
        li { margin: 0.5rem 0; }
        a { text-decoration: none; color: #0066cc; }
        a:hover { text-decoration: underline; }
        footer { margin-top: 3rem; font-size: 0.8rem; color: #999; }
    </style>
</head>
<body>
    <h1>🗂 過去のニュース一覧</h1>
    <ul>
"""

    for f in date_files:
        date_str = f[5:-5]  # news_YYYY-MM-DD.html → YYYY-MM-DD
        html += f'        <li><a href="{f}">{date_str} のニュース</a></li>\n'

    html += """    </ul>
    <footer>提供：まいにゅ〜</footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ 履歴一覧ページ生成完了：{output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    history_dir = os.path.join(base_dir, "../public/history")
    output_path = os.path.join(history_dir, "index.html")
    generate_history_index(history_dir, output_path)
