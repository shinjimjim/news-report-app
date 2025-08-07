# db/save_headlines.py
from datetime import date
from sqlalchemy import exists # 重複チェックのために使用。
from db.settings import SessionLocal # SessionLocal は SQLAlchemyのセッション（DBとのやりとりの窓口）を作るための関数やクラス
from db.models import Headline
from utils.categorize import categorize_title

def save_headlines(source_name, headlines, category=None):
    # DBセッション開始
    session = SessionLocal() # session はデータベースとのやりとりに使う「操作窓口」です。この session を使って、クエリ実行・追加・削除などができます。
    try:
        # 各見出しについて繰り返し処理
        for title, url in headlines:
            # 重複チェック（同じURLが既にあるか）
            if session.query(exists().where(Headline.url == url)).scalar(): # Headline.url == url の条件で、すでに同じURLがDBに存在するか確認。scalar() はTrue/Falseで結果を返します。
                continue # 存在していれば continue でスキップ（重複保存を防止）。
            category = categorize_title(title)
            # 新しいレコードを作成
            headline = Headline(
                source=source_name,
                title=title,
                url=url,
                date=date.today(),
                category=category
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
