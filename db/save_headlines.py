from datetime import date
from sqlalchemy import exists # 重複チェックのために使用。
from db.settings import SessionLocal # SessionLocal は SQLAlchemyのセッション（DBとのやりとりの窓口）を作るための関数やクラス
from db.models import Headline
from utils.categorize import categorize_title
from utils.extract import fetch_article_body

# --- 要約モジュールの両対応（plus が無ければ旧版にフォールバック） ---
try:
    from utils.summarize import generate_summary_plus as _gen_plus  # 新
except Exception:
    _gen_plus = None
from utils.summarize import generate_summary as _gen_basic  # 旧

def _summarize(title: str, source_name: str, body_text: str):
    """
    generate_summary_plus() があればそれを使い、
    無ければ generate_summary() の結果から最小限の形に寄せる。
    戻り値: (summary_text, keywords_csv, comment_text, comment_type, quality)
    """
    if _gen_plus:
        # 新版ありの場合
        data = _gen_plus(
            title=title,
            source=source_name,
            max_chars=90,        # HTMLで読みやすい長さ
            body=body_text or "",
            comment_max=60,      # 「編集部メモ」短め
            temperature=0.2,
        )
        summary = (data.get("summary") or "").strip() or None
        kws_csv = ",".join(data.get("keywords") or []) or None # keywordsは配列想定なので",".join(...)でCSV化（DBに文字列で保存するための簡単な表現）。
        comment = (data.get("comment") or "").strip() or None
        ctype = (data.get("comment_type") or "").strip() or None
        quality = (data.get("quality") or "ok").strip()
        return summary, kws_csv, comment, ctype, quality # 返ってきたJSONから、必要キー（summary | keywords | comment | comment_type | quality）を安全に取り出す（get()→strip()→空ならNone）。

    # 新版なし（旧版フォールバック）の場合
    data = _gen_basic(
        title=title,
        source=source_name,
        max_chars=60,
        body=body_text or "",
    )
    summary = (data.get("summary") or "").strip() or None
    kws_csv = ",".join(data.get("keywords") or []) or None
    quality = (data.get("quality") or "ok").strip() # quality…出力品質メタ。例："ok" | "shortened" | "fallback" など。運用で「要約が短縮し過ぎ」や「本文無しのfallback」などを後で分析できる。
    return summary, kws_csv, None, None, quality # 旧版はcomment/comment_typeが無いのでNoneにする。

def save_headlines(source_name, headlines, category=None):
    """
    headlines: iterable[(title, url)]
    """
    # DBセッション開始
    session = SessionLocal() # session はデータベースとのやりとりに使う「操作窓口」です。この session を使って、クエリ実行・追加・削除などができます。
    try:
        today = date.today()
        for idx, (title, url) in enumerate(headlines, start=1):
            # 1) 重複（URL）チェック
            if session.query(exists().where(Headline.url == url)).scalar(): # exists().where(Headline.url == url) で「このURLの行がある？」をブールでチェック。
                continue # 既存なら continue でスキップ → 多重保存を防ぐ。

            # 2) カテゴリ自動判定（引数 category を上書きしないよう別名）
            detected_category = categorize_title(title) # categorize_title(title) の結果をdetected_categoryに。下のレコード作成では detected_category if detected_category else category なので、自動判定が空/nullのときだけ引数category（外側で決めたカテゴリ）を使う設計。

            # 3) 本文抽出（失敗しても空文字で続行）
            body_text = ""
            try:
                body_text = fetch_article_body(url) or "" # 例：trafilatura → 取れなければBeautifulSoupで汎用セレクタを当てに行く関数（プロジェクト別ファイル）。
            except Exception as e:
                print(f"[extract WARN] {source_name} :: {title} -> {e}") # ここはネットワークも絡むので、失敗しても落とさず続行（空文字でOK）。ログにWARNを出す。

            # 4) 要約＋独自コメント
            try:
                summary_text, keywords_csv, comment_text, comment_type, quality = _summarize(
                    title=title, source_name=source_name, body_text=body_text
                ) # _summarize()で、本文の有無に応じて品質が変動し得る（qualityで追跡）。
            except Exception as e:
                print(f"[summarize ERROR] {source_name} :: {title}\n  -> {repr(e)}") # エラー時はログ出し・"fallback"扱いで空値を入れて続行（全体バッチを止めない）。
                summary_text, keywords_csv, comment_text, comment_type, quality = None, None, None, None, "fallback"

            # 5) レコード作成
            h = Headline(
                source=source_name,
                title=title,
                url=url,
                date=today,
                category=detected_category if detected_category else category,
                summary=summary_text,
                keywords=keywords_csv,
                comment=comment_text,
                comment_type=comment_type,
                quality=quality,
                body=body_text or None,
            ) # ORMオブジェクト Headline(...) を作って session.add()。フィールドのNULL許容：summary/keywords/comment/comment_type/body は状況により None になるため、モデル側で nullable=True や Text 型を想定。
            session.add(h)

            # 6) バルクコミット（100件ごとに一度。必要なければ削ってOK）
            if idx % 100 == 0: 
                session.commit()

        session.commit()
    except Exception as e: # 予期せぬ例外で rollback() → エラーログ → finallyで確実にclose()。
        session.rollback()
        print("❌ エラー:", e)
    finally:
        session.close()
