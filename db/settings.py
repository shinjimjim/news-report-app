# SQLAlchemy を使って MySQL データベースへ接続するための設定
import os # os: 環境変数を取得するために使うPython標準ライブラリ。
from dotenv import load_dotenv # load_dotenv(): .env ファイルの内容を 環境変数として読み込む関数（python-dotenv パッケージによる機能）
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# .envを読み込む
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 接続URLを構築
# これは SQLAlchemy 用の 接続URL（Connection String） を作ってます。
  # mysql+pymysql://：MySQL に pymysql を使って接続する指定
  # {ユーザー}:{パスワード}@{ホスト}:{ポート}/{DB名}：接続情報
  # ?charset=utf8mb4：日本語や絵文字対応のための文字コード指定
# mysql+pymysql://myuser:secretpass@localhost:3306/news_db?charset=utf8mb4
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# データベース接続エンジンを作成
engine = create_engine(DATABASE_URL, echo=False) # create_engine() は SQLAlchemy の コアとなる DB接続オブジェクト を作成します。echo=False：SQL文のログ出力をオフ（開発中なら True にしてもOK）
# DBセッションを作成可能にする
  # sessionmaker(...) は SQLAlchemy の DB操作のための「セッション（操作窓口）」を作る関数。
  # autocommit=False：明示的に .commit() が必要
  # autoflush=False：自動で変更をDBに送らない（必要なら .flush() を手動で呼ぶ）
  # bind=engine：このセッションは engine に接続されていることを示す
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
