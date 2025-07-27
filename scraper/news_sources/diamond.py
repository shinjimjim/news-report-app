import requests
from bs4 import BeautifulSoup

def get_diamond_headlines():
    url = 'https://diamond.jp/'
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    headlines = []

    # 上位5件のランキング記事のタイトルとURLを取得
    for i in range(1, 6):
        selector = (
            f"body > main > div.l-2col.top-fv > div.top-subcolumn > "
            f"div.m-ranking > div.m-ranking__container > div.c-tab-pannel.js-tab-pannel.--is-active > "
            f"div > a:nth-child({i})"
        )
        a_tag = soup.select_one(selector)
        if not a_tag:
            continue

        title_tag = a_tag.select_one('article > div.m-ranking-article__info > h3')
        href = a_tag.get('href')

        if title_tag and href:
            title = title_tag.get_text(strip=True)
            if not href.startswith('http'):
                href = f"https://diamond.jp{href}"
            headlines.append((title, href))

    return headlines
