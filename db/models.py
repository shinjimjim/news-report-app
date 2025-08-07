# SQLAlchemy：Pythonでデータベース操作をオブジェクト指向で扱えるようにするライブラリ
from sqlalchemy.ext.declarative import declarative_base # declarative_base() は、**「モデル定義の基礎クラス」**を作る関数
from sqlalchemy import Column, Integer, String, Text, Date # データ型やカラム定義のためのインポート

# ベースクラスを作る
Base = declarative_base() # これで Base という変数が、すべてのテーブル定義の親クラスになります。

# テーブル定義
class Headline(Base): # Base を継承しているので、SQLAlchemyがこのクラスをテーブルとして認識します。
    __tablename__ = 'headlines' # __tablename__ = 'headlines'：このクラスはデータベース上では 'headlines' という名前のテーブルとして扱われます。

    # 各カラムの定義
    id = Column(Integer, primary_key=True, autoincrement=True) # 主キー（primary key）です。autoincrement=True：レコードを追加するたびに自動で連番になります。
    source = Column(String(255)) # ニュースソースの名前（例：NHK、Yahoo、CNNなど）最大255文字までの文字列として保存されます。
    title = Column(Text) # ニュースの見出しタイトル、長めの文字列になる可能性があるため Text 型が使われています。
    url = Column(Text) # ニュース記事のリンクURL、これも長くなる可能性があるため Text 型。
    date = Column(Date) # 記事の掲載日や収集日などを記録するための日付フィールド（例：2025-08-04）
    category = Column(String(50))