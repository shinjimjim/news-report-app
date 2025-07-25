from datetime import datetime # datetime: 現在の日時を取得・整形するために使います（発行日時の表示用）。
import os # os: ファイルパスを動的に生成するために使います。
from fetch_news import get_headlines
import re # re: 正規表現（文字列処理）を行うPython標準ライブラリです。

# 番号付きテキストから番号を除去する（"1. ○○" → "○○"）
def remove_leading_number(text):
    return re.sub(r'^\d+[\.、．]?\s*', '', text) # ^: 文字列の先頭。\d+: 1桁以上の数字（例: 1, 12, 123）。[\.、．]?: 「.」「、」「．」のいずれかが1個あるかないか（?）。\s*: 空白（スペースやタブなど）を0個以上

# HTML出力関数
def generate_html(path):
    # 見出しと日時の取得
    headlines = get_headlines()[:5] # [:5]: 先頭5件だけを使います（トップ5）
    now = datetime.now().strftime('%Y/%m/%d %H:%M') # datetime.now().strftime()：現在日時を「2025/07/25 01:45」形式で取得します。

    # HTMLの冒頭テンプレート
    html = f"""<!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <title>今日のニュース（トップ5）</title>
                <style>
                    body {{ font-family: sans-serif; padding: 2rem; max-width: 800px; margin: auto; }}
                    h1 {{ font-size: 1.8rem; color: #333; }}
                    p.date {{ color: #777; font-size: 0.9rem; }}
                    ol {{ padding-left: 1.2rem; }}
                    li {{ margin: 1rem 0; }}
                    a {{ text-decoration: none; color: #0066cc; }}
                    a:hover {{ text-decoration: underline; }}
                    footer {{ margin-top: 3rem; color: #aaa; font-size: 0.8rem; }}
                </style>
            </head>
            <body>
                <h1>📰 今日の主要ニュース（トップ5）</h1>
                <p class="date">発行日時：{now}</p>
                <ol>
            """
            # f"""...{now}..."""：f文字列で、現在の日時をHTMLに埋め込みます。
            # <ol>：順序付きリスト（自動で「1.」「2.」と番号が付きます）

    # 各ニュース見出しを <li> タグとして追加
    for title, url in headlines:
        clean_headline = remove_leading_number(title) # remove_leading_number(...)：番号を削除
        html += f'        <li><a href="{url}" target="_blank" rel="noopener">{clean_headline}</a></li>\n'
        # <li>...</li>：1件ずつリストとしてHTMLに追加

    # HTMLの末尾を閉じる
    html += """    </ol>
                <footer>提供：まいにゅ〜</footer>
            </body>
            </html>"""

    # HTMLファイルに書き込む
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ HTMLレポート生成完了：{path}")

# 実行部分
if __name__ == "__main__": # __name__ == "__main__"：このファイルが直接実行されたときだけ下記を実行
    output_path = os.path.join(os.path.dirname(__file__), "../public/news_report.html") # os.path.dirname(__file__)：このファイルのあるディレクトリ
    generate_html(output_path)
