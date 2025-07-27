import requests # requests：ウェブページにアクセスするためのライブラリ。指定URLのHTMLデータを取得するのに使う。
from bs4 import BeautifulSoup # bs4 の BeautifulSoup：HTMLを解析し、特定の要素（見出しやリンク）を抽出するためのライブラリ。

def get_nhk_headlines():
    # HTMLの取得と解析
    url = 'https://www3.nhk.or.jp/news/' # NHKのトップページにアクセスします。
    res = requests.get(url) # res は取得結果（HTML全体）です。
    res.encoding = res.apparent_encoding # 文字化け防止のため、自動検出されたエンコーディング（文字コード）に強制的に設定します。NHKはUTF-8でない場合もあるので重要です。
    soup = BeautifulSoup(res.text, 'html.parser') # HTML文字列をBeautifulSoupで解析して、HTMLタグのツリー構造を持つオブジェクトに変換します。

    # ニュース見出しの抽出
    headlines = [] # 見出しを保存するリストを初期化します。
    for a in soup.select("a[href^='/news/html']"): # <a> タグの中で、href 属性が /news/html から始まるリンクをすべて抽出します。NHKのニュースリンクのパターンは /news/html/20250727_xxxxx.html のようになっています。
        text = a.get_text(strip=True) # <a> タグの中のテキスト（見出し）を取り出し、前後の空白を除去します。
        href = a.get('href') # リンク先の相対URL（例: /news/html/20250727_xxxxx.html）を取得します。
        # 見出しを条件付きで追加
        if text and len(text) > 10: # 見出しが空でないかつ、**ある程度の長さ（10文字以上）**があるものだけを対象とします。
            full_url = f"https://www3.nhk.or.jp{href}" # 相対URLを完全なURLに変換します。
            if (text, full_url) not in headlines: # 同じ見出しとURLの組が既に含まれていない場合だけ、追加します（重複防止）。
                headlines.append((text, full_url))
        # 最大5件までに制限
        if len(headlines) >= 5: # 見出しを5件取得したら、処理を終了します。
            break
    
    # 見出しリストを返す
    return headlines # 見出しとURLのペアを5件まで格納したリストを返します。
