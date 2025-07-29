from selenium import webdriver # selenium：ブラウザを自動操作するライブラリ（Chromeを操作）
from selenium.webdriver.chrome.options import Options # Options：Chromeの起動オプション（例：画面を表示しない等）
from selenium.webdriver.common.by import By # By：要素検索の条件指定（CSSセレクタなど）
from selenium.webdriver.chrome.service import Service #：Service	ChromeDriverのサービスを管理
from webdriver_manager.chrome import ChromeDriverManager # ChromeDriverManager：自動で適切なChromeDriverをインストール・管理
import time # time：待機時間（time.sleep）を設定するための標準ライブラリ

def get_cnn_headlines():
    # Chrome起動オプションの設定
    options = Options()
    options.add_argument("--headless")  # 画面を表示しないモード（サーバー上でも動く）
    options.add_argument("--no-sandbox") # サンドボックス無効（Linux環境で必要なことがある）
    options.add_argument("--disable-dev-shm-usage") # 共有メモリの問題回避（Dockerなどで有効）

    # Chromeドライバ起動（自動インストール付き）
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) # ChromeDriverManager().install()：環境に合ったChromeDriverを自動取得。webdriver.Chrome(...)：ヘッドレスChromeを起動

    # CNNのトップページへアクセス
    url = "https://www.cnn.co.jp/"
    driver.get(url)
    time.sleep(2)  # ページの動的読み込みを考慮して2秒待機

    # 空のリストを用意して結果を格納
    headlines = []

    # ニュース見出しの取得
    try:
        # 1位の見出しとURL
        title_1 = driver.find_element(By.CSS_SELECTOR, # title_1.text.strip()：記事タイトル（前後の空白除去）
            "body > div.pg-wrapper > div > section:nth-child(5) > div.category-wrapper > div.cb-l3.cb-rank > div > a > div.cd-ttl"
        )
        href_1 = driver.find_element(By.CSS_SELECTOR,
            "body > div.pg-wrapper > div > section:nth-child(5) > div.category-wrapper > div.cb-l3.cb-rank > div > a"
        ).get_attribute("href") # .get_attribute("href")：リンクURLを取得
        headlines.append((title_1.text.strip(), href_1)) # headlines.append(...)：タプルでリストに追加

        # 2～4位の見出しとURL（ループ処理）。2〜4位は ul > li:nth-child({i}) > a の形式で配置されている
        for i in range(1, 4):
            a = driver.find_element(By.CSS_SELECTOR,
                f"body > div.pg-wrapper > div > section:nth-child(5) > div.category-wrapper > div.cb-l3.cb-rank > ul > li:nth-child({i}) > a"
            )
            text = a.text.strip()
            href = a.get_attribute("href")
            headlines.append((text, href)) # 各 a 要素からテキストとリンクを取得して追加

    # 失敗時のエラーハンドリング
    except Exception as e: # 見出し取得中にエラーが出ても、アプリがクラッシュしないように例外処理
        print("⚠️ CNN.co.jp の取得に失敗:", e)

    # ブラウザを閉じてリソース解放
    driver.quit()
    # 結果を返す
    return headlines
