# DBに溜めたニュース（headlines）をカテゴリ別にまとめて、1枚のHTML（reports/index.html）に吐き出す
from datetime import date
from pathlib import Path
from sqlalchemy import create_engine, text
from db.settings import engine as _engine  # 既存の設定を使う想定（なければ適宜修正）
from db.settings import SessionLocal
from db.models import Headline

# OUTPUT_DIR = Path("reports")
OUTPUT_DIR = Path("public") / "reports" # Path("reports")… 相対パス ./reports。
OUTPUT_DIR.mkdir(parents=True, exist_ok=True) # 無ければ mkdir(..., exist_ok=True) で作成。
OUTPUT_HTML = OUTPUT_DIR / "index.html" # OUTPUT_HTML… 出力ファイルの絶対パスは OUTPUT_HTML.resolve() で確認可能。

# HTML テンプレ（head / foot）
HTML_HEAD = """<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>毎朝ニュースレポート</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,"Noto Sans JP","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;line-height:1.6;margin:24px;background:#0b0b0f;color:#e9e9ee}
  a{color:#9ecbff;text-decoration:none}
  a:hover{text-decoration:underline}
  .wrap{max-width:980px;margin:0 auto}
  h1{font-size:24px;margin-bottom:8px}
  .meta{opacity:.7;font-size:12px;margin-bottom:24px}
  .cat{display:inline-block;padding:2px 8px;border-radius:999px;background:#1b1b25;font-size:12px;margin-left:8px}
  ul{list-style:none;padding:0;margin:0}
  li{padding:14px 0;border-bottom:1px solid #222}
  .title{font-weight:600}
  .summary{margin:6px 0 2px 0;font-size:14px;opacity:.95}
  .keywords{font-size:12px;opacity:.75}
  .source{opacity:.8;font-size:12px}
  </style>
</head>
<body><div class="wrap">
"""

HTML_FOOT = """
</div></body></html>
"""

# データ取得（カテゴリごとに上限付き）
def fetch_latest(limit_per_category: int = 50):
    """
    カテゴリ別に新しい順で取得（簡易版）。
    """
    session = SessionLocal()
    try:
        # 直近日付でまとめて拾い、カテゴリ→新しい順に並べ替え（メモリ側で）
        rows = session.query(Headline).order_by(Headline.id.desc()).limit(2000).all() # 「新しい順に上から2000件だけ」取ります（id desc ＝ AUTO_INCREMENT を新しさの近似として利用）。
        bucket = {}
        for r in rows:
            key = r.category or "その他" # r.category or "その他"：DB値がNULL/空の場合のフォールバック。
            bucket.setdefault(key, []) # その2000件を Python側でカテゴリごとに詰める。
            if len(bucket[key]) < limit_per_category: # 各カテゴリは limit_per_category 件まで。
                bucket[key].append(r)
        return bucket
    finally:
        session.close()

# HTML を組み立てる
def build_html():
    # データの取得と日付の整形
    bucket = fetch_latest(limit_per_category=50) # bucket は {"政治": [Headline, ...], "経済": [...], ...} の辞書（カテゴリ→記事配列）。各カテゴリで 最大50件 に制限済み（重たくならないように）。
    today = date.today().strftime("%Y-%m-%d") # today は見出しに入れるための「YYYY-MM-DD」文字列。

    # HTMLの先頭（ヘッダ）を parts に積む
    parts = [HTML_HEAD, f"<h1>毎朝ニュースレポート</h1>",
             f'<div class="meta">{today} 生成</div>']

    # カテゴリ順は見やすさ重視で一例
    preferred = ["政治","経済","ビジネス","金融・マネー","国際","気象・災害","地域・地方",
                 "社会","交通・事故","暮らし","医療・健康","教育・受験",
                 "スポーツ","エンタメ","科学・文化","テクノロジー","IT・インターネット","AI・生成AI","セキュリティ・犯罪","労働・雇用","食・グルメ","ペット・動物","旅行・観光","その他"]

    # preferred の中で 実際にデータがあるものだけを並べる。+ bucket にあるけど preferred に無い 未知カテゴリ を末尾に追加。つまり、想定外の新カテゴリがDBに来ても落ちずに表示される。
    order = [c for c in preferred if c in bucket] + [c for c in bucket.keys() if c not in preferred]

    # 各カテゴリのHTMLブロック生成
    for cat in order:
        parts.append(f"<h2>{cat} <span class='cat'>{len(bucket[cat])}件</span></h2>") # 見出し <h2> にカテゴリ名と件数バッジ。
        # <ul><li>…</li></ul> で記事リストを作る。
        parts.append("<ul>")
        for h in bucket[cat]:
            parts.append("<li>")
            parts.append(f"<a class='title' href='{h.url}' target='_blank' rel='noopener'>{h.title}</a>") # タイトルは <a> でリンク化。target="_blank" は新規タブ、rel="noopener" はセキュリティ＆パフォーマンス（開いた先から window.opener を使われない）。
            if h.summary: # summary（要約）があれば1行表示。
                parts.append(f"<div class='summary'>{h.summary}</div>")
            if h.keywords: # keywords は DBで「カンマ区切り」想定 → split(',') → トリム → 空要素除去 → #tag 風に整形して表示。
                parts.append(f"<div class='keywords'>#{' #'.join([k.strip() for k in h.keywords.split(',') if k.strip()])}</div>")
            parts.append(f"<div class='source'>{h.source} / {h.date}</div>") # source/date は出典と日付の情報欄。
            parts.append("</li>")
        parts.append("</ul>")

    # フッタを閉じてファイルに書く
    parts.append(HTML_FOOT)
    OUTPUT_HTML.write_text("\n".join(parts), encoding="utf-8")
    print(f"✅ HTML written: {OUTPUT_HTML.resolve()}")

if __name__ == "__main__":
    build_html()
