# ライブラリ
import requests # requests：ウェブページにアクセスするためのライブラリ。指定URLのHTMLデータを取得するのに使う。
from bs4 import BeautifulSoup # bs4 の BeautifulSoup：HTMLを解析し、特定の要素（見出しやリンク）を抽出するためのライブラリ。

# 関数定義
def get_headlines(): # この関数は、Yahoo!ニュースのトップページからニュース見出しをリスト形式で返します。
    # Yahoo!ニュースのHTML取得
    url = 'https://news.yahoo.co.jp' # url：取得対象のWebサイトのURL。
    res = requests.get(url) # res = requests.get(url)：このURLにHTTPリクエストを送り、HTML全体を取得します。
    # 文字化け対策
    res.encoding = res.apparent_encoding  # YahooのHTMLは文字コードがUTF-8とは限らないので、レスポンスのエンコーディングを自動検出されたもの（apparent_encoding）に設定することで文字化けを防ぐ。
    # HTML解析
    soup = BeautifulSoup(res.text, 'html.parser') # res.text：取得したHTMLの中身（文字列）を取得。BeautifulSoup：それをパース（解析）して検索しやすくする。html.parser：Python標準のHTML解析器を使用。

    # 見出しを格納するリスト
    headlines = [] # ニュースの見出しをためておく空のリスト。
    # ニュース見出しの抽出
    for a in soup.find_all('a', href=True): # soup.find_all('a', href=True)：<a href="...">リンク</a> のタグをすべて取得。href=Trueは、href属性を持っている<a>タグだけを対象にする。
        href = a['href'] # href：リンク先URL（文字列）。
        text = a.get_text(strip=True) # text：リンクの中にあるテキストを抽出し、前後の空白も除去。

        # 条件に合うものだけ見出しとして採用
        if '/articles/' in href and text and len(text) > 10: # '/articles/' in href：Yahooニュースの個別記事のURLに /articles/ が含まれているため、ニュース記事リンクだけを抽出。text が空でなく、len(text) > 10：短すぎるリンクやナビゲーションメニューを除外する目的。
            headlines.append(text)

        # 上限5件に達したら終了
        if len(headlines) >= 5:
            break

    # 最終的な結果
    return headlines # 条件を満たしたニュース見出し（最大5件）のリストを返す。
