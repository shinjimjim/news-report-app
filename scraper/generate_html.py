from datetime import datetime, date, timedelta # datetime: 現在の日時を取得・整形するために使います（発行日時の表示用）。
import os # os: ファイルパスを動的に生成するために使います。
import re # re: 正規表現（文字列処理）を行うPython標準ライブラリです。
# 既存フォールバック用（今日分がDBに無いときだけ使う）
from scraper.fetch_news import get_all_headlines
# DBから headline を取る
from db.settings import SessionLocal
from db.models import Headline

# 番号付きテキストから番号を除去する（"1○○" → "○○"）
def remove_leading_number(text):
    if isinstance(text, str) and text[:1].isdigit(): # isdigit() で先頭文字が数字かどうか確認。
        return text[1:] # text[1:] でその1文字目を取り除いた文字列を返す。
    return text

# DBから最近のニュースを取得する関数
def _fetch_from_db_for_recent(days: int = 1, max_per_source: int = 5):
    """
    直近 days 日に該当する headlines をDBから取得して、{source: [Headline,...]}で返す。
    """
    session = SessionLocal()
    try:
        since = date.today() - timedelta(days=days-1)  # 今日を含む days 分のデータを抽出
        rows = (
            session.query(Headline)
            .filter(Headline.date >= since)
            .order_by(Headline.id.desc())
            .all()
        )
        bucket = {}
        for r in rows:
            bucket.setdefault(r.source, []) # bucket.setdefault() でソース別に分類
            # ソースごとに最大 max_per_source 件まで
            if (max_per_source is None) or (len(bucket[r.source]) < max_per_source):
                bucket[r.source].append(r)
        return bucket
    finally:
        session.close()

# HTML出力関数
def generate_html(main_path, archive_path): # この関数では、HTMLレポートを2か所に保存します：main_path: 最新のニュース用（例：public/news_report.html）archive_path: 履歴保存用（例：public/history/news_2025-07-27.html）
    # 見出しと日時の取得
    all_news = get_all_headlines()  # [(source_name, [(title, url), ...]), ...]
    # 日付・時刻の取得とフォーマット
    now = datetime.now()
    now_str = now.strftime('%Y/%m/%d %H:%M') # now_str: HTMLに表示する発行日時（人間向け）
    date_str = now.strftime('%Y-%m-%d') # date_str: ファイル名やアーカイブに使う（機械向け）

    # 例: 直近2日・各ソース最大10件表示（上限なしにするなら max_per_source=None）
    bucket = _fetch_from_db_for_recent(days=7, max_per_source=5)

    # もし今日分がDBに1件もなければ、既存のフローにフォールバック
    # （初回実行や収集失敗時の保険）
    use_db = True
    if not bucket:
        use_db = False
        all_news = get_all_headlines()  # [(source, [(title,url),..]),..]

    # 表示したいソース順（任意）：DBのキー順だとバラつくので固定順を用意
    preferred_sources = [
        "NHKニュース", "時事通信", "ITmedia", "東洋経済オンライン", "ダイヤモンド・オンライン",
        "ABEMA TIMES", "Sponichi Annex", "INTERNET Watch", "BBCニュース", "CNN.co.jp"
    ]
    if use_db:
        ordered_sources = [s for s in preferred_sources if s in bucket] \
                          + [s for s in bucket.keys() if s not in preferred_sources]
    else:
        ordered_sources = [s for s, _ in all_news]
    # DBモードなら、bucketに存在するものだけ順序適用
    # ordered_sources = (
    #     [s for s in preferred_sources if (use_db and s in bucket)]
    #     if use_db else
    #     [s for s, _ in all_news]
    # )

    # HTMLの冒頭テンプレート（ヘッダー）
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日のニュース（{date_str}）</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Noto Sans JP', sans-serif;
            margin: 0;
            padding: 2rem 1rem;
            background-color: #f0f2f5;
            color: #333;
        }}
        .container {{
            max-width: 720px;
            margin: auto;
            background: #fff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 0.5rem;
            color: #111;
        }}
        .date {{
            font-size: 0.9rem;
            color: #888;
            margin-bottom: 1.5rem;
        }}
        ol {{
            padding-left: 1.2rem;
        }}
        li {{
            margin-bottom: 1rem;
            line-height: 1.6;
        }}
        a {{
            color: #007acc;
            text-decoration: none;
            font-weight: bold;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        footer {{
            margin-top: 3rem;
            font-size: 0.85rem;
            text-align: center;
            color: #aaa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 今日の主要ニュース（{date_str}）</h1>
        <p class="date">発行日時：{now_str}</p>
        <ol>
"""
# モバイル対応（<meta name="viewport">あり）
# <ol>：順序付きリスト（自動で「1.」「2.」と番号が付きます）

    # --- 本体描画 ---
    # DBモード：bucket[source] は Headline の配列
    if use_db:
        for source_name in ordered_sources:
            items = bucket.get(source_name, [])
            if not items:
                continue
            html += f"<h2>{source_name}</h2>\n<ol>\n"
            for r in items: # r は Headline インスタンス
                clean_title = remove_leading_number(r.title or "")
                html += f'  <li><a href="{r.url}" target="_blank" rel="noopener">{clean_title}</a>'
                # 要約
                if r.summary: # r.summary や r.keywords はDBに保存された情報
                    html += f'<div class="summary">{r.summary}</div>'
                # キーワード（カンマ区切り → #タグ風）
                if r.keywords:
                    tags = ' #'.join([k.strip() for k in r.keywords.split(',') if k.strip()]) # キーワードは # をつけてハッシュタグ風に表示
                    if tags:
                        html += f'<div class="keywords">#{tags}</div>'
                html += "</li>\n"
            html += "</ol>\n"
    else:

        # フォールバック：従来のスクレイプ結果をそのまま表示（要約は出ない）
        # 各ニュース見出しを <li> タグとしてHTMLリストに追加
        for source_name, headlines in all_news:
            html += f"<h2>{source_name}</h2>\n<ol>\n"
            for title, url in headlines:
                clean_title = remove_leading_number(title) # remove_leading_number(...)：番号を削除
                html += f'  <li><a href="{url}" target="_blank" rel="noopener">{clean_title}</a></li>\n'
            html += "</ol>\n"

    # HTMLの末尾を閉じる
    html += """    <footer>提供：まいにゅ〜</footer>
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
