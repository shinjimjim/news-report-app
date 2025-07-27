import os # os：ファイル・ディレクトリ操作に使います（ファイル一覧取得、パス結合など）。
import re # re：正規表現モジュールです。ファイル名が「news_2025-07-27.html」のように日付形式になっているかをチェックします。

def generate_history_index(history_dir, output_path): # history_dir：ニュースHTMLファイルが保存されているフォルダ（例：public/history）。output_path：生成する index.html の出力パス
    # ファイル一覧取得＆フィルター
    files = sorted(os.listdir(history_dir), reverse=True) # os.listdir(...)：ディレクトリ内のファイル名一覧を取得。sorted(..., reverse=True)：ファイル名で降順にソート（新しい日付が先頭）

    # news_YYYY-MM-DD.html 形式にマッチするものだけ抽出
    date_files = [
        f for f in files
        if re.match(r'news_\d{4}-\d{2}-\d{2}\.html$', f) # \d{4}-\d{2}-\d{2}：YYYY-MM-DD の形式
    ]

    # HTMLテンプレートの先頭部分、見出しと<ul>（リスト）の開始タグも含む
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

    # 日付付きリンクを追加
    for f in date_files:
        date_str = f[5:-5]  # news_YYYY-MM-DD.html → YYYY-MM-DD
        html += f'        <li><a href="{f}">{date_str} のニュース</a></li>\n' # html に <li><a href=...> 形式でリンクを追加していく

    # HTMLフッターを追加
    html += """    </ul>
    <footer>提供：まいにゅ〜</footer>
</body>
</html>"""
# <ul> の閉じタグ、フッターを追加

    # 書き出し処理
    os.makedirs(os.path.dirname(output_path), exist_ok=True) # 出力先フォルダがなければ作成（exist_ok=True で既にあってもエラーにならない）
    with open(output_path, 'w', encoding='utf-8') as f: # 作成したHTML文字列をファイルに保存
        f.write(html)

    print(f"✅ 履歴一覧ページ生成完了：{output_path}")

# 実行部分
if __name__ == "__main__":
    base_dir = os.path.dirname(__file__) # __file__：このPythonスクリプトのファイルパス
    history_dir = os.path.join(base_dir, "../public/history") # base_dir：このスクリプトがあるディレクトリ
    output_path = os.path.join(history_dir, "index.html") # history_dir：HTMLが保存されている場所（例：public/history）。output_path：index.html の出力先
    generate_history_index(history_dir, output_path)
