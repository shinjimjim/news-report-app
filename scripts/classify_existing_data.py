# scripts/classify_existing_data.py

import os
import sys
from dotenv import load_dotenv
from utils.categorize import categorize_title
import mysql.connector

# .env 読み込み
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path=env_path)

# DB接続情報
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

def update_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # データ取得
        cursor.execute("SELECT id, title FROM headlines")
        rows = cursor.fetchall()

        updated_count = 0

        for row in rows:
            id, title = row
            category = categorize_title(title)
            
            # UPDATE実行
            cursor.execute(
                "UPDATE headlines SET category = %s WHERE id = %s",
                (category, id)
            )
            updated_count += 1

        conn.commit()
        print(f"✅ カテゴリ更新完了: {updated_count}件")

    except Exception as e:
        print("❌ エラー:", e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    update_categories()
