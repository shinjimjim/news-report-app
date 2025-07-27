import requests # requests: WebページのHTMLを取得するためのライブラリ。
from bs4 import BeautifulSoup # BeautifulSoup: HTMLを解析して、特定のタグや要素を簡単に取り出すためのライブラリ（bs4パッケージの中にある）。

def get_jiji_headlines():
    # 時事通信のHTMLを取得
    url = 'https://www.jiji.com/' # url にアクセスするためのリクエストを送信します。
    res = requests.get(url) # res に、HTTPレスポンス（HTMLデータなど）が格納される。
    res.encoding = res.apparent_encoding # 自動的に文字エンコーディングを検出して設定（日本語ページの文字化け対策）。
    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(res.text, 'html.parser') # res.text: HTMLの中身（文字列）を取得。html.parser: Python標準のHTML解析器を使う。soup はHTML全体をパースしたオブジェクト。

    # ニュース見出しの要素を取得
    selectors = [
        '#BoxGenre > section.Ranking.BoxGenreBlock > div.RankingContents > dl > dd:nth-child(2) > a', # 抽出したいセレクタ（2, 4, 6, 8, 10 番目の dd の中の a）
        '#BoxGenre > section.Ranking.BoxGenreBlock > div.RankingContents > dl > dd:nth-child(4) > a',
        '#BoxGenre > section.Ranking.BoxGenreBlock > div.RankingContents > dl > dd:nth-child(6) > a',
        '#BoxGenre > section.Ranking.BoxGenreBlock > div.RankingContents > dl > dd:nth-child(8) > a',
        '#BoxGenre > section.Ranking.BoxGenreBlock > div.RankingContents > dl > dd:nth-child(10) > a'
    ]

    # 見出しとURLを抽出・整形
    headlines = []
    for selector in selectors:
        tag = soup.select_one(selector) # select_one(selector)：CSSセレクタで1つだけ要素を取得します
        if tag:
            title = tag.get_text(strip=True) # リンクテキスト（ニュースタイトル）を取得。前後の空白は削除。
            href = tag.get('href') # <a>タグのリンク先URLを取得。

            # 相対リンクの補完（相対パスなら絶対URLに変換）
            if href and not href.startswith("http"): # href が http で始まっていない（＝相対パス）の場合は、https://www.jiji.com を前に付けて絶対URLに変換。
                href = 'https://www.jiji.com' + href

            # 見出しリストに追加
            if title and href:
                headlines.append((title, href)) # title と href の両方が存在する場合のみ、タプルとして headlines に追加。

    # 最終的に見出しリストを返す
    return headlines
