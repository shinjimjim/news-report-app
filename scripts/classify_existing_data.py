import os # os: パス結合やファイル位置取得に使用
import sys # sys: 現状は未使用（将来的にCLI引数やパス操作に使う余地）
from dotenv import load_dotenv # dotenv.load_dotenv: .env ファイルから環境変数を読み込むため
from utils.categorize import categorize_title
import mysql.connector # mysql.connector: 公式の MySQL Python コネクタ

# .env 読み込み
env_path = os.path.join(os.path.dirname(__file__), '../.env') # スクリプトファイルの場所（__file__）から相対的に ../.env を指す
load_dotenv(dotenv_path=env_path)

# DB接続情報（辞書）
DB_CONFIG = {
    'host': os.getenv('DB_HOST'), # os.getenv で .env → 環境変数から読み込み
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4' # charset='utf8mb4' は絵文字や多言語対応に必須
}

# メイン処理
def update_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG) # DBへ接続。失敗すると例外→exceptへ。
        cursor = conn.cursor() # SQLを実行するためのカーソル。

        # データ取得
        cursor.execute("SELECT id, title FROM headlines") # 全件をメモリに読み込み（件数が多いと重い）。
        rows = cursor.fetchall()

        updated_count = 0

        for row in rows: # ループで categorize_title(title) を呼ぶ
            id, title = row
            category = categorize_title(title)
            
            # UPDATE実行
            cursor.execute(
                "UPDATE headlines SET category = %s WHERE id = %s", # プレースホルダ %s でパラメータバインド（SQLインジェクション安全）。
                (category, id)
            )
            updated_count += 1

        conn.commit() # まとめてトランザクション確定。ここまでの UPDATE がDBに反映。
        print(f"✅ カテゴリ更新完了: {updated_count}件")

    except Exception as e:
        print("❌ エラー:", e)
    finally: # finally でクリーンアップ。
        if conn.is_connected():
            cursor.close()
            conn.close() # conn.is_connected() を見て cursor/conn をクローズ。

# エントリポイント
if __name__ == '__main__': # スクリプトとして実行されたときだけ update_categories() を走らせる（モジュールimport時は実行されない）。
    update_categories()
