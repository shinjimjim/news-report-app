from datetime import date
from sqlalchemy import exists # 重複チェックのために使用。
from db.settings import SessionLocal # SessionLocal は SQLAlchemyのセッション（DBとのやりとりの窓口）を作るための関数やクラス
from db.models import Headline
from utils.categorize import categorize_title
from utils.summarize import generate_summary  # 要約生成
from utils.extract import fetch_article_body

def save_headlines(source_name, headlines, category=None):
    # DBセッション開始
    session = SessionLocal() # session はデータベースとのやりとりに使う「操作窓口」です。この session を使って、クエリ実行・追加・削除などができます。
    try:
        # 各見出しについて繰り返し処理
        for title, url in headlines:
            # 重複チェック（同じURLが既にあるか）
            if session.query(exists().where(Headline.url == url)).scalar(): # Headline.url == url の条件で、すでに同じURLがDBに存在するか確認。scalar() はTrue/Falseで結果を返します。
                continue # 存在していれば continue でスキップ（重複保存を防止）。
            # カテゴリ自動判定
            category = categorize_title(title)
            # タイトルから超短い要約を生成（本文なしでも機能する簡易版）
            # --- 本文抽出 ---
            body_text = fetch_article_body(url)  # 空文字の可能性あり
            try:
                s = generate_summary(title=title, source=source_name, max_chars=60, body=body_text)
                summary_text = s["summary"]
                keywords_csv = ",".join(s["keywords"]) if s.get("keywords") else None
            except Exception as e:
                print(f"[summarize ERROR] {source_name} :: {title}\n  -> {repr(e)}")
                summary_text = None
                keywords_csv = None
            # 新しいレコードを作成
            headline = Headline(
                source=source_name,
                title=title,
                url=url,
                date=date.today(),
                category=category,
                summary=summary_text,
                keywords=keywords_csv,
                body=body_text or None
            ) # Headline オブジェクトを作成。データベースに追加する前の一時的なオブジェクトです。
            # レコード追加
            session.add(headline) # 作成した headline を「セッションに登録」。まだデータベースには書き込まれていません（次の commit() で確定します）。
        # 保存の確定（コミット）
        session.commit()
    except Exception as e:
        session.rollback() # 途中でエラーが出たら session.rollback() で変更をキャンセル。
        print("❌ エラー:", e)
    finally:
        session.close() # 成功・失敗に関わらず最後にセッションを閉じます（リソース解放のため）。
