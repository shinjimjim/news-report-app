# ライブラリ
import requests # requests：ウェブページにアクセスするためのライブラリ。指定URLのHTMLデータを取得するのに使う。
from bs4 import BeautifulSoup # bs4 の BeautifulSoup：HTMLを解析し、特定の要素（見出しやリンク）を抽出するためのライブラリ。
from news_sources.yahoo import get_yahoo_headlines
from news_sources.nhk import get_nhk_headlines

def get_all_headlines():
    result = []

    # ソースごとにまとめる
    result.append(("Yahooニュース", get_yahoo_headlines()))
    result.append(("NHKニュース", get_nhk_headlines()))

    return result  # [(source_name, [(title, url), ...]), ...]
