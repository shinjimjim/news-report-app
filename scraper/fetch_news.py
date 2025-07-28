# ライブラリ
import requests # requests：ウェブページにアクセスするためのライブラリ。指定URLのHTMLデータを取得するのに使う。
from bs4 import BeautifulSoup # bs4 の BeautifulSoup：HTMLを解析し、特定の要素（見出しやリンク）を抽出するためのライブラリ。
from news_sources.nhk import get_nhk_headlines
from news_sources.jiji import get_jiji_headlines
from news_sources.itmedia import get_itmedia_headlines
from news_sources.toyokeizai import get_toyokeizai_headlines
from news_sources.diamond import get_diamond_headlines
from news_sources.abema import get_abema_headlines
from news_sources.sponichi import get_sponichi_headlines
from news_sources.internet_watch import get_internet_watch_headlines

def get_all_headlines():
    return [
        ("NHKニュース", get_nhk_headlines()),
        ("時事通信", get_jiji_headlines()),
        ("ITmedia", get_itmedia_headlines()),
        ("東洋経済オンライン", get_toyokeizai_headlines()),
        ("ダイヤモンド・オンライン", get_diamond_headlines()),
        ("ABEMA TIMES", get_abema_headlines()),
        ("Sponichi Annex", get_sponichi_headlines()),
        ("INTERNET Watch", get_internet_watch_headlines())
    ]
