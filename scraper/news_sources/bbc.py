from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_bbc_headlines():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = 'https://www.bbc.com/japanese'
    driver.get(url)

    headlines = []

    try:
        # 最初の見出しが現れるまで待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#main-wrapper > div > main > div > div > section:nth-child(8) > ol > li:nth-child(1) > div > div.bbc-14zb6im > a"))
        )

        # li:nth-child(n) をループで切り替えて5件取得
        for i in range(1, 6):
            selector = f"#main-wrapper > div > main > div > div > section:nth-child(8) > ol > li:nth-child({i}) > div > div.bbc-14zb6im > a"
            element = driver.find_element(By.CSS_SELECTOR, selector)
            title = element.text.strip()
            href = element.get_attribute('href')
            full_url = href if href.startswith("http") else "https://www.bbc.com" + href

            if title:
                headlines.append((title, full_url))

    except Exception as e:
        print("⚠️ BBC Japan の取得に失敗:", e)

    driver.quit()
    return headlines
