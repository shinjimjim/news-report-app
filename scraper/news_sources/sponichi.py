import requests
from bs4 import BeautifulSoup

def get_sponichi_headlines():
    url = 'https://www.sponichi.co.jp/'
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    headlines = []

    # ランキング1〜5位のリスト項目を取得
    for i in range(1, 6):
        selector = (
            f"#documentWrapper > main > div > aside > div:nth-child(2) > "
            f"div:nth-child(2) > ul.active.tab-contents > li:nth-child({i}) > a"
        )
        a_tag = soup.select_one(selector)
        if not a_tag:
            continue

        title_tag = a_tag.select_one('div > p')
        href = a_tag.get("href")

        if title_tag and href:
            title = title_tag.get_text(strip=True)
            if not href.startswith("http"):
                href = f"https://www.sponichi.co.jp{href}"
            headlines.append((title, href))

    return headlines
