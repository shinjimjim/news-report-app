# SQLAlchemyを使ってテーブルを自動的にデータベースに作成する処理
from db.models import Base # Base は 「どんなテーブルが定義されているか」情報を記録しているオブジェクト
from db.settings import engine # engine は「どこに、どうやって接続するか」を知っているオブジェクト

# モデル Headline(Base) が定義している headlines テーブルが、MySQLデータベースに作成される
  # Base.metadata：すべてのテーブル定義の「設計図の集合体」のようなもの。
  # .create_all(...)：その設計図に従って、まだ存在しないテーブルを作成する。
  # bind=engine：どのデータベースに作成するかを指定（接続情報）。
Base.metadata.create_all(bind=engine)
