from datetime import datetime # datetime: 現在の日時を取得・整形するために使います（発行日時の表示用）。
import os # os: ファイルパスを動的に生成するために使います。
from fetch_news import get_headlines
import re # re: 正規表現（文字列処理）を行うPython標準ライブラリです。

# 番号付きテキストから番号を除去する（"1○○" → "○○"）
def remove_leading_number(text):
    if isinstance(text, str) and text[:1].isdigit(): # isdigit() で先頭文字が数字かどうか確認。
        return text[1:] # text[1:] でその1文字目を取り除いた文字列を返す。
    return text

# HTML出力関数
def generate_html(main_path, archive_path): # この関数では、HTMLレポートを2か所に保存します：main_path: 最新のニュース用（例：public/news_report.html）archive_path: 履歴保存用（例：public/history/news_2025-07-27.html）
    # 見出しと日時の取得
    headlines = get_headlines()[:5] # [:5]: 先頭5件だけを使います（トップ5）
    # 日付・時刻の取得とフォーマット
    now = datetime.now()
    now_str = now.strftime('%Y/%m/%d %H:%M') # now_str: HTMLに表示する発行日時（人間向け）
    date_str = now.strftime('%Y-%m-%d') # date_str: ファイル名やアーカイブに使う（機械向け）

    # HTMLの冒頭テンプレート（ヘッダー）
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日のニュース（{date_str}）</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
            margin: 0;
            padding: 1.5rem;
            max-width: 768px;
            margin-left: auto;
            margin-right: auto;
            background-color: #f9f9f9;
            color: #333;
        }}
        h1 {{
            font-size: 1.6rem;
            margin-bottom: 0.5rem;
        }}
        .date {{
            font-size: 0.9rem;
            color: #777;
            margin-bottom: 1.5rem;
        }}
        ol {{
            padding-left: 1.2rem;
        }}
        li {{
            margin: 1rem 0;
            line-height: 1.5;
        }}
        a {{
            text-decoration: none;
            color: #007acc;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        footer {{
            margin-top: 3rem;
            font-size: 0.8rem;
            color: #999;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>📰 今日の主要ニュース（{date_str}）</h1>
    <p class="date">発行日時：{now_str}</p>
    <ol> 
"""
# モバイル対応（<meta name="viewport">あり）
# <ol>：順序付きリスト（自動で「1.」「2.」と番号が付きます）

    # 各ニュース見出しを <li> タグとしてHTMLリストに追加
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
    for path in [main_path, archive_path]:
        os.makedirs(os.path.dirname(path), exist_ok=True) # os.makedirs(...): ディレクトリが存在しない場合は自動作成（history/など）
        with open(path, 'w', encoding='utf-8') as f: # open(..., 'w'): ファイルを上書きモードで開き、UTF-8で保存
            f.write(html)

    print(f"✅ HTML生成完了: {main_path}")
    print(f"📦 履歴保存完了: {archive_path}")

# 実行部分
if __name__ == "__main__": # __name__ == "__main__"：このファイルが直接実行されたときだけ下記を実行
    # main_path と archive_path の設定
    base_dir = os.path.dirname(__file__) # os.path.dirname(__file__)：このファイルのあるディレクトリ
    public_dir = os.path.join(base_dir, "../public") # ../public: HTMLを保存する公開ディレクトリ
    history_dir = os.path.join(public_dir, "history") # history: 日付ごとに履歴を残すためのサブフォルダ

    today_str = datetime.now().strftime('%Y-%m-%d')
    latest_path = os.path.join(public_dir, "news_report.html") # latest_path: 上書きされる最新版HTML
    archive_path = os.path.join(history_dir, f"news_{today_str}.html") # archive_path: 毎日別名で保存される履歴HTML

    generate_html(latest_path, archive_path)
