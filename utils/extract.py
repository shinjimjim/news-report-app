# URLから本文テキストを安全に抜き出す
import trafilatura # trafilatura: HTML から本文抽出に強いライブラリ（見出し/本文/不要要素の切り分けが賢い）。
import requests # requests: HTTP取得。
from bs4 import BeautifulSoup # BeautifulSoup: HTML構文木を作り、要素抽出用。

# URL を受け取り、本文テキスト（失敗時は空文字）を返す関数。
def fetch_article_body(url: str) -> str:
    try:
        # trafilatura の fetch_url でHTMLを取得。
        downloaded = trafilatura.fetch_url(url)
        if downloaded: # 取得できたら extract で本文抽出。
            text = trafilatura.extract(
                downloaded,
                include_comments=False, # include_comments=False：コメント欄などを除外。
                include_tables=False # include_tables=False：表はノイズになりやすいので除外。
            )
            if text and len(text.strip()) > 80: # 抽出テキストの 長さが80文字超 なら本文とみなして返す。
                return text.strip()
    except Exception as e: # trafilatura 側の例外はログを出して握りつぶす（アプリが落ちないようにするため）。
        print(f"[trafilatura ERROR] {url} :: {e}")

    # BeautifulSoup フォールバック
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}) # requests で再取得。ここでは timeout を明示（10秒）。
        res.encoding = res.apparent_encoding # apparent_encoding でレスポンスの実体に合わせたエンコーディングを設定（日本語サイトでも文字化け回避しやすい）。
        # よく本文が入る 代表的なセレクタ を順に試す。
        soup = BeautifulSoup(res.text, "html.parser")
        for sel in ["article", "main", "[role=main]", ".articleBody", ".article", "#main"]: # article, main, role=main はHTML5の意味論的タグ/ロール。.articleBody や .article、#main はニュースサイトで頻繁に使われるクラス/ID。
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(" ", strip=True) # get_text(" ", strip=True) はテキストの抽出時に余計な空白をトリム、ブロック間をスペースで連結して読みやすくする（改行が消えても語がくっつかない）。
                if txt and len(txt) > 80: # ここでも 80文字超 なら本文として採用。
                    return txt
        # セレクタで取れないサイト向けの最後の手段。
        txt = soup.get_text(" ", strip=True)
        return txt if len(txt) > 120 else "" # ページ全体のテキストを拾って 120文字超 なら返す（全体だとナビやメニュー文言が混じりやすいので、しきい値を少し高めに設定）。
    except Exception as e: # ネットワーク/解析エラーでも落とさず空文字を返す。
        print(f"[requests ERROR] {url} :: {e}")
        return ""
