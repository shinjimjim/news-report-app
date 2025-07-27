# ライブラリ
import requests # requests：ウェブページにアクセスするためのライブラリ。指定URLのHTMLデータを取得するのに使う。
from bs4 import BeautifulSoup # bs4 の BeautifulSoup：HTMLを解析し、特定の要素（見出しやリンク）を抽出するためのライブラリ。
from news_sources.yahoo import get_yahoo_headlines
from news_sources.nhk import get_nhk_headlines
from news_sources.jiji import get_jiji_headlines
from news_sources.itmedia import get_itmedia_headlines


def get_all_headlines():
    return [
        ("Yahooニュース", get_yahoo_headlines()),
        ("NHKニュース", get_nhk_headlines()),
        ("時事通信", get_jiji_headlines()),
        ("ITmedia", get_itmedia_headlines())
    ]
