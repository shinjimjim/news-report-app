# 外部ライブラリの読み込み
from reportlab.pdfgen import canvas # reportlab.pdfgen.canvas：PDFのページを描画するためのツール（文字・図形・画像の配置など）
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont # pdfmetrics, TTFont：日本語フォントをPDFで使えるように登録
from reportlab.lib.pagesizes import A4 # A4：用紙サイズ（A4）を指定
from datetime import datetime # datetime：発行日時を現在時刻で取得
import os # os：ファイルパス操作用（OSに依存しないパスを作る）
import textwrap # textwrap：長い文章を指定幅で自動改行するためのツール
import re # re：正規表現によるテキスト前処理
from fetch_news import get_headlines

# 日本語フォント登録
font_name = 'IPAexGothic' # IPAexGothic：日本語対応の無料フォント。
font_path = os.path.join(os.path.dirname(__file__), '../fonts/ipaexg.ttf') # os.path.join：どのOSでも使えるようにフォントファイルのパスを生成。
pdfmetrics.registerFont(TTFont(font_name, font_path)) # pdfmetrics.registerFont：PDFでこのフォントを使えるように登録。

# テキストを強制改行する関数
def force_wrap(text, width=45): # width=45は、1行に最大45文字で自動改行。
    return '\n'.join(textwrap.wrap(text, width))

# PDF生成関数
def generate_pdf(path):
    # キャンバスとレイアウト初期設定
    c = canvas.Canvas(path, pagesize=A4) # canvas.Canvas：描画キャンバス（1ページ）を作成
    width, height = A4
    margin = 50 # margin：上下左右の余白（ここでは50pt）
    available_width = width - 2 * margin - 20  # 右余白安全確保
    font_size = 10
    line_height = 18
    y = height - margin # y：縦方向の描画位置（上から下へ描画する）

    #  ヘッダー描画関数
    def draw_header():
        nonlocal y # nonlocal y は、外の変数 y をこの関数内でも更新可能にします。
        c.setFont(font_name, 16)
        c.drawString(margin, y, "今日の主要ニュース（トップ5）")
        y -= 24
        c.setFont(font_name, font_size)
        c.drawString(margin, y, f"発行日: {datetime.now().strftime('%Y/%m/%d %H:%M')}") # ヘッダーにはタイトルと日付を描画します。
        y -= 30

    # フッター描画関数
    def draw_footer():
        c.setFont(font_name, 10)
        c.drawString(margin, 40, "提供：まいにゅ〜")

    draw_header()

    # ニュース見出しを取得＆描画
    headlines = get_headlines()[:5]  # fetch_news.py の get_headlines() 関数から最大5件の見出しを取得。
    c.setFont(font_name, font_size)

    # 1文字目が数字なら削除
    def clean_headline(text):
        if isinstance(text, str) and text[:1].isdigit():
            return text[1:]
        return text

    # 各見出しをループで処理
    for i, (headline_text, _) in enumerate(headlines[:5], 1): # i は見出し番号（1〜5）
        headline = clean_headline(headline_text)
        # 番号付き見出しをラップ処理
        wrapped_text = force_wrap(headline, width=45)
        lines = wrapped_text.split('\n')

        # ページ切り替え処理
        required_height = line_height * (len(lines) + 1) + 6
        if y - required_height < 60:
            draw_footer()
            c.showPage()
            y = height - margin
            draw_header()
            c.setFont(font_name, font_size) # 下に余白が足りない場合、新ページに移動。

        # 見出しの描画：番号と本文を段落で描画し、行ごとに縦位置をずらしていきます。
        c.drawString(margin, y, f"{i}.") # 番号
        y -= line_height
        for line in lines:
            c.drawString(margin + 20, y, line) # 本文（インデント20pt）
            y -= line_height
        y -= 6  # ニュース間余白

    draw_footer()
    c.save()
    print(f"✅ PDF生成完了：{path}")

# 実行ブロック
if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "../public/news_report.pdf")
    generate_pdf(output_path) # スクリプトを直接実行した場合にだけ、generate_pdf() を呼び出してPDFを作成します。
