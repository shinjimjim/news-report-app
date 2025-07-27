import requests
from bs4 import BeautifulSoup

def get_abema_headlines():
    url = 'https://times.abema.tv/'
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    headlines = []

    # ランキング上位5件（1〜5）を順に取得
    for i in range(1, 6):
        selector = (
            f"body > div.page > div.l-wrapper.--ad-gate > div.l-contents > div.l-main-side-wrapper > "
            f"aside > div:nth-child(3) > section > ul.c-ranking__list.--tab.is-show.js-tab-block > "
            f"li:nth-child({i}) > a"
        )
        a_tag = soup.select_one(selector)
        if not a_tag:
            continue

        title_tag = a_tag.select_one("div:nth-child(1) > div > p > span")
        href = a_tag.get("href")

        if title_tag and href:
            title = title_tag.get_text(strip=True)
            if not href.startswith("http"):
                href = f"https://times.abema.tv{href}"
            headlines.append((title, href))

    return headlines
