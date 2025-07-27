import requests
from bs4 import BeautifulSoup

def get_toyokeizai_headlines():
    url = 'https://toyokeizai.net/'
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')

    headlines = []

    # メインニュース枠のセレクタをもとに取得（例: トップページの注目記事）
    for i in range(1, 6):
        selector = f"#gtm_h24_{i} > span.title"
        title_tag = soup.select_one(selector)
        link_tag = soup.select_one(f"#gtm_h24_{i}")

        if title_tag and link_tag and link_tag.name == 'a':
            title = title_tag.get_text(strip=True)
            href = link_tag.get('href')
            if href and not href.startswith('http'):
                href = f'https://toyokeizai.net{href}'
            headlines.append((title, href))

    return headlines
