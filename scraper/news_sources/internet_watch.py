from selenium import webdriver # webdriver：Chromeなどのブラウザを自動操作するためのSeleniumのメイン機能
from selenium.webdriver.chrome.service import Service # Service：ChromeDriverの実行サービスを管理
from selenium.webdriver.common.by import By # By：要素を検索する方法を指定する（例：CSS_SELECTOR, ID, CLASS_NAME など）
from selenium.webdriver.chrome.options import Options # Options：Chromeの起動オプションを設定する（例：ヘッドレスモードなど）
from selenium.webdriver.support.ui import WebDriverWait # WebDriverWait：要素が表示されるまでの「明示的な待機」を行う
from selenium.webdriver.support import expected_conditions as EC # expected_conditions as EC：「ある条件になるまで待つ」ための条件定義
from webdriver_manager.chrome import ChromeDriverManager # ChromeDriverManager：ChromeDriverのパスを自動管理してくれる便利ライブラリ

def get_internet_watch_headlines():
    # Chromeの設定と起動
    options = Options() # Options()：ブラウザ起動時のオプションを設定。
    options.add_argument("--headless")  # --headless：Chromeを「画面なし」で起動する（サーバーや自動実行向け）。
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) # ChromeDriverManager().install()：自動的にChromeDriverをダウンロード＆パス設定。webdriver.Chrome(...)：Chromeブラウザを自動操作用に起動。

    # サイトにアクセス
    url = 'https://internet.watch.impress.co.jp/'
    driver.get(url)

    # ニュース見出し格納用リスト
    headlines = [] # 最終的に (タイトル, URL) のタプルをここに格納する。
    # 明示的な待機と取得処理
    try:
        WebDriverWait(driver, 10).until( # WebDriverWait(..., 10)：最大10秒間待つ。
            EC.presence_of_element_located((By.CSS_SELECTOR, "#site-access-ranking-ul-latest li.rank-1 span > a")) # presence_of_element_located(...)：指定した要素がDOMに出現するまで待機。このコードは「ランキング1位」の見出しが出るまで待ちます。
        )

        # 見出し1〜5位を取得
        for i in range(1, 6):  # i を 1〜5 までループ。
            selector = f"#site-access-ranking-ul-latest li.rank-{i} span > a"
            element = driver.find_element(By.CSS_SELECTOR, selector) # li.rank-1 ～ li.rank-5 という構造の a 要素をそれぞれ探す。
            title = element.text.strip() # element.text：リンク文字列（ニュースタイトル）を取得。
            href = element.get_attribute('href') # element.get_attribute('href')：リンク先URLを取得。
            if title and href:
                headlines.append((title, href)) # headlines に (タイトル, URL) を追加。

    # エラーハンドリング
    except Exception as e: # 要素が見つからない、接続に失敗した、などの例外が発生したら、警告を出す。
        print("⚠️ INTERNET Watch の取得に失敗:", e)

    # 終了処理と結果返却
    driver.quit() # driver.quit()：ブラウザを閉じる（メモリ解放）。
    return headlines # return headlines：取得した見出しのリストを返す。
