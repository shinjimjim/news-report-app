const express = require('express'); // expressモジュールを読み込む。Node.jsでWebサーバーを簡単に作れる
const path = require('path'); // パス操作用モジュールを読み込む。OSに依存しないファイルパスの操作ができます。
const app = express(); // Expressアプリケーション（サーバー）を作成

// /public パスで静的ファイルを公開する設定
app.use('/public', express.static(path.join(__dirname, '../public'))); // express.static() は指定フォルダ内のファイル（PDFや画像など）をそのまま公開できるようにします。path.join(__dirname, '../public') は public フォルダまでの絶対パスを作っています。__dirname は現在のファイルのあるディレクトリ。その1つ上の ../public フォルダを指します。

// GET / ：リクエスト（トップページ）へのルート定義
app.get('/', (req, res) => {
  // HTMLを返す処理
  res.send(`
    <h1>最新ニュースレポート</h1>
    <p><a href="/public/news_report.pdf" target="_blank">PDFを表示</a></p>
  `); // target="_blank" → 別タブでPDFを開く
});

// ポート3000でサーバーを起動し、起動確認メッセージを出力
app.listen(3000, () => {
  console.log('✅ サーバー起動： http://localhost:3000');
});
