# 外部ライブラリの読み込み
from reportlab.pdfgen import canvas # reportlab.pdfgen.canvas：PDFのページを描画するためのツール（文字・図形・画像の配置など）
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont # pdfmetrics, TTFont：日本語フォントをPDFで使えるように登録
from reportlab.lib.pagesizes import A4 # A4：用紙サイズ（A4）を指定
from datetime import datetime # datetime：発行日時を現在時刻で取得
from reportlab.lib.colors import blue
import os # os：ファイルパス操作用（OSに依存しないパスを作る）
import textwrap # textwrap：長い文章を指定幅で自動改行するためのツール
import re # re：正規表現によるテキスト前処理
from scraper.fetch_news import get_all_headlines

# 日本語フォント登録
font_name = 'IPAexGothic' # IPAexGothic：日本語対応の無料フォント。
font_path = os.path.join(os.path.dirname(__file__), '../fonts/ipaexg.ttf') # os.path.join：どのOSでも使えるようにフォントファイルのパスを生成。
pdfmetrics.registerFont(TTFont(font_name, font_path)) # pdfmetrics.registerFont：PDFでこのフォントを使えるように登録。

# テキストを強制改行する関数
def force_wrap(text, width=45): # width=45は、1行に最大45文字で自動改行。
    return '\n'.join(textwrap.wrap(text, width))

# 番号付きテキストから番号を除去する（"1○○" → "○○"）
def clean_headline(text):
    if isinstance(text, str) and text[:1].isdigit(): # isdigit() で先頭文字が数字かどうか確認。
        return text[1:] # text[1:] でその1文字目を取り除いた文字列を返す。
    return text

# PDF生成関数
def generate_pdf(path):
    # キャンバスとレイアウト初期設定
    c = canvas.Canvas(path, pagesize=A4) # canvas.Canvas：描画キャンバス（1ページ）を作成
    width, height = A4
    margin = 50 # margin：上下左右の余白（ここでは50pt）
    font_size = 10
    line_height = 18
    y = height - margin # y：縦方向の描画位置（上から下へ描画する）

    #  ヘッダー描画関数
    def draw_header():
        nonlocal y # nonlocal y は、外の変数 y をこの関数内でも更新可能にします。
        c.setFont(font_name, 16)
        c.drawString(margin, y, "今日の主要ニュース")
        y -= 24
        c.setFont(font_name, font_size)
        c.drawString(margin, y, f"発行日: {datetime.now().strftime('%Y/%m/%d %H:%M')}") # ヘッダーにはタイトルと日付を描画します。
        y -= 30

    # フッター描画関数
    def draw_footer():
        c.setFont(font_name, 10)
        c.drawString(margin, 40, "提供：まいにゅ〜")

    draw_header()
    c.setFont(font_name, font_size)

    # ニュース見出しを取得＆描画
    all_news = get_all_headlines()  # [(source_name, [(title, url), ...]), ...]

    # セクションごとの見出し描画ループ
    for source_name, headlines in all_news: # get_all_headlines() から受け取ったデータのループ。
        # ページ余白チェック（セクション描画前）
        if y - 40 < 60: # 40pt分の余白が確保できないとき、改ページ。y は現在の描画位置（下方向に減っていく）。改ページ後に y を初期値に戻してヘッダー再描画。
            draw_footer()
            c.showPage()
            y = height - margin
            draw_header()

        # ニュースソース名の描画（セクションヘッダー）
        c.setFont(font_name, 12) # 見やすくするためフォントサイズは12pt。
        c.drawString(margin, y, f"【{source_name}】") # 【Yahooニュース】 や 【NHK】 のように表示。
        y -= 22 # 描画後は縦位置 y を下げる（次のテキストの描画位置）。
        c.setFont(font_name, font_size)

        # 各ニュース記事（最大5件）のループ
        for i, (headline_text, url) in enumerate(headlines[:5], 1): # 各ソースから最大5件まで取得。headline_text はニュースのタイトル文字列、url はURL。
            # 見出し整形・改行処理
            headline = clean_headline(headline_text) # clean_headline() で先頭番号を削除（例：1記事タイトル → 記事タイトル）。
            lines = force_wrap(headline, width=45).split('\n') # force_wrap() で45文字ごとに強制改行 → 複数行に。
            required_height = line_height * (len(lines) + 1) + 6 # required_height はこの見出しの描画に必要な縦スペース：本文行数 × 行高（18pt）＋ 番号行1行分 ＋ 余白（6pt）

            # 改ページチェック（個別見出しごと）
            # この見出しを描くのに十分なスペースがないとき → 改ページ。ページが変わっても、同じニュースソースが続いていることがわかるように、【Yahooニュース（続き）】 と表示する工夫。
            if y - required_height < 60:
                draw_footer()
                c.showPage()
                y = height - margin
                draw_header()
                c.setFont(font_name, 12)
                c.drawString(margin, y, f"【{source_name}（続き）】")
                y -= 22
                c.setFont(font_name, font_size)

            # 番号付き見出しの描画
            c.drawString(margin, y, f"{i}.") # 見出し番号（1., 2. など）を描画。

            # 本文行の描画
            for line in lines:
                text_x = margin + 20
                text_y = y

                # リンクっぽい青い文字で描画
                c.setFillColor(blue)
                c.drawString(text_x, text_y, line) # 各改行済みの行をインデント（20pt）付きで描画。

                # 下線を引く（細い青線）
                text_width = pdfmetrics.stringWidth(line, font_name, font_size) # テキスト幅の測定
                c.setStrokeColor(blue)
                c.setLineWidth(0.5)
                c.line(text_x, text_y - 1, text_x + text_width, text_y - 1)

                # クリック領域としてURLリンクを設定
                if url:
                    c.linkURL(
                        url, # url：開くべきリンク（http〜）
                        (text_x, text_y, text_x + text_width, text_y + line_height), # (x1, y1, x2, y2)：リンク範囲の四角形（左下〜右上）
                        relative=0, # relative=0：絶対座標を使う（ページ全体基準）
                        thickness=0  # クリック領域の枠線は非表示
                    )

                y -= line_height # 1行描画ごとに y を減らして次行へ。

            # 描画が終わったら色を黒に戻す
            c.setFillColor("black")

            y -= 6 # 次の見出しとの間にちょっとしたスペースを確保。

    # 最後のフッター＆保存
    draw_footer()
    c.save()
    print(f"✅ PDF生成完了：{path}")

# 実行ブロック
if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "../public/news_report.pdf")
    generate_pdf(output_path) # スクリプトを直接実行した場合にだけ、generate_pdf() を呼び出してPDFを作成します。
