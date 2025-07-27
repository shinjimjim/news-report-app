import requests
from bs4 import BeautifulSoup

def get_itmedia_headlines():
    url = 'https://www.itmedia.co.jp/'
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    headlines = []

    # ランキング上位5件を取得（rank1〜rank5）
    for i in range(1, 6):
        selector = f"#colBoxRanking > div.colBoxIndex > div > ul > li.rank{i} > a"
        a_tag = soup.select_one(selector)

        if a_tag:
            title = a_tag.get_text(strip=True)
            href = a_tag.get('href')

            if href and not href.startswith('http'):
                href = f"https://www.itmedia.co.jp{href}"

            headlines.append((title, href))

    return headlines
