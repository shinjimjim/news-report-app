import argparse # argparse：コマンドライン引数を扱う標準ライブラリ
import os # os：ファイルパス操作のために使う
from scraper.generate_report import generate_pdf
from scraper.generate_html import generate_html
from scraper.generate_history_index import generate_history_index
from datetime import datetime # datetime：今日の日付の取得に使用
from scraper.fetch_news import get_all_headlines
from db.save_headlines import save_headlines
from scripts.build_html import build_html

# get_all_headlines() で全ニュースソースの見出しを収集して、それをDB保存用関数 save_headlines(source_name, headlines) にソースごと渡して保存する制御ループ
all_news = get_all_headlines()
for source_name, headlines in all_news:
    save_headlines(source_name, headlines)

def main():
    parser = argparse.ArgumentParser(description="ニュースレポート自動生成CLI") # argparse.ArgumentParser(...)→ CLIに説明をつける
    parser.add_argument("command", choices=["run"], help="コマンド: run = PDF+HTML生成＋index作成") # add_argument("command", choices=["run"])→ 実行コマンドを "run" に限定。
    args = parser.parse_args() # args.command→ 引数が "run" のときだけ実行する仕組み

    if args.command == "run":
        # パスの準備
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # __file__ はこのファイル（cli.py）のパス。dirname(__file__) でディレクトリ（scripts/）を取得。.. で親ディレクトリ（news-report-app/）へ移動。abspath(...) で絶対パスに変換
        # script_dir = os.path.dirname(__file__)
        # report_dir = os.path.abspath(os.path.join(script_dir, "../../news-report"))
        # history_dir = os.path.join(report_dir, "history")

        # 出力先のファイルパス定義
        public_dir = os.path.join(project_root, "public")
        history_dir = os.path.join(public_dir, "history")
        latest_html = os.path.join(public_dir, "news_report.html")
        pdf_path = os.path.join(public_dir, "news_report.pdf")
        index_path = os.path.join(history_dir, "index.html")
        today_str = datetime.now().strftime('%Y-%m-%d')
        archive_html = os.path.join(history_dir, f"news_{today_str}.html")
        # latest_html = os.path.join(report_dir, "news_report.html")
        # pdf_path = os.path.join(report_dir, "news_report.pdf")
        # index_path = os.path.join(report_dir, "index.html")

        # HTML・PDF・index.html の順に生成
        print("📄 HTML生成中...")
        generate_html(latest_html, archive_html)

        print("📰 PDF生成中...")
        generate_pdf(pdf_path)

        print("📚 履歴一覧(index.html)生成中...")
        generate_history_index(history_dir, index_path) # public/history/ にある HTML 一覧を読み込み、リンク付きの index.html を作る

        print("📊 カテゴリ別ニュース一覧(reports/index.html)生成中...")
        build_html()

        print("✅ 完了しました！")

# エントリーポイント
if __name__ == "__main__":
    main()
