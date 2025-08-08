# ライブラリ
import requests # requests：ウェブページにアクセスするためのライブラリ。指定URLのHTMLデータを取得するのに使う。
from datetime import datetime
from bs4 import BeautifulSoup # bs4 の BeautifulSoup：HTMLを解析し、特定の要素（見出しやリンク）を抽出するためのライブラリ。
from scraper.news_sources.nhk import get_nhk_headlines
from scraper.news_sources.jiji import get_jiji_headlines
from scraper.news_sources.itmedia import get_itmedia_headlines
from scraper.news_sources.toyokeizai import get_toyokeizai_headlines
from scraper.news_sources.diamond import get_diamond_headlines
from scraper.news_sources.abema import get_abema_headlines
from scraper.news_sources.sponichi import get_sponichi_headlines
from scraper.news_sources.internet_watch import get_internet_watch_headlines
from scraper.news_sources.bbc import get_bbc_headlines
from scraper.news_sources.cnn import get_cnn_headlines
from db.settings import SessionLocal
from db.models import Headline

# ニュースをDBに保存して (id, title, url) の形で返す
def save_and_return_ids(source_name, headlines):
    # SQLAlchemyの Session を生成。
    session = SessionLocal() # SessionLocal は sessionmaker から作られている（はずの）ファクトリ。ここで得た session を通じて DBへINSERT/COMMIT などを行います。
    results = [] #後で (id, title, url) を入れて返すための空リスト。
    for title, url in headlines: #渡された headlines を1件ずつ処理。ここは title, url の 2タプル で来る前提です。
        obj = Headline(source=source_name, title=title, url=url, date=datetime.now().date()) # 各列へ値をセットして インスタンスを作成。
        session.add(obj) # obj をセッションに登録（まだDBには反映されていない、ステージング状態）。
        session.commit() # DBへ確定反映（COMMIT）。主キー（id のオートインクリメント）が確定します。
        session.refresh(obj)  # 挿入後にidを取得。refresh() で確実に同期を取っています。
        results.append((obj.id, title, url)) # DB採番済みの id と、元の title, url をタプルで保存。
    session.close() # セッションを必ずクローズ（接続リーク防止）。
    return results

def get_all_headlines():
    return [
        ("NHKニュース", get_nhk_headlines()),
        ("時事通信", get_jiji_headlines()),
        ("ITmedia", get_itmedia_headlines()),
        ("東洋経済オンライン", get_toyokeizai_headlines()),
        ("ダイヤモンド・オンライン", get_diamond_headlines()),
        ("ABEMA TIMES", get_abema_headlines()),
        ("Sponichi Annex", get_sponichi_headlines()),
        ("INTERNET Watch", get_internet_watch_headlines()),
        ("BBCニュース", get_bbc_headlines()),
        ("CNN.co.jp", get_cnn_headlines())
    ]
