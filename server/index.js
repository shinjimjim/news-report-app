const express = require('express'); // expressモジュールを読み込む。Node.jsでWebサーバーを簡単に作れる
const path = require('path'); // パス操作用モジュールを読み込む。OSに依存しないファイルパスの操作ができます。
const app = express(); // Expressアプリケーション（サーバー）を作成
const fs = require('fs');

app.set('view engine', 'ejs'); // ejsをテンプレートエンジンとして使用
app.set('views', path.join(__dirname, 'views')); // テンプレートのディレクトリ

// /public パスで静的ファイルを公開する設定
app.use('/public', express.static(path.join(__dirname, '../public'))); // express.static() は指定フォルダ内のファイル（PDFや画像など）をそのまま公開できるようにします。path.join(__dirname, '../public') は public フォルダまでの絶対パスを作っています。__dirname は現在のファイルのあるディレクトリ。その1つ上の ../public フォルダを指します。

// トップページ（最新PDF＋履歴5件）
app.get('/', (req, res) => {
  const historyDir = path.join(__dirname, '../public/history');

  fs.readdir(historyDir, (err, files) => {
    if (err) return res.status(500).send('履歴フォルダの読み込みに失敗しました');

    // PDFだけ取得して新しい順にソート
    // const pdfs = files.filter(f => f.endsWith('.pdf')).sort().reverse();
    // // 最新PDF（public直下の固定ファイル想定）
    // const latestPdf = 'news_report.pdf';
    // // 履歴は最大5件
    // const recentReports = pdfs.slice(0, 5);

    // HTMLファイルのみ取得（index.htmlは除外）
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f !== 'index.html')
      .sort()
      .reverse();

    const latestHtml = 'news_report.html'; // 最新版（public直下にある想定）
    const recentReports = htmlFiles.slice(0, 5);

    res.render('index', { latestHtml, recentReports });
  });
});

// app.get('/history', (req, res) => {
//   const historyDir = path.join(__dirname, '../public/history');
//   fs.readdir(historyDir, (err, files) => {
//     if (err) return res.status(500).send('読み込みエラー');
//     const pdfs = files.filter(f => f.endsWith('.pdf'));
//     res.render('history', { reports: pdfs });
//   });
// });

// 履歴ページ（全履歴表示）
app.get('/history', (req, res) => {
  const historyDir = path.join(__dirname, '../public/history');

  fs.readdir(historyDir, (err, files) => {
    if (err) return res.status(500).send('履歴フォルダの読み込みに失敗しました');

    // const htmls = files.filter(f => f.endsWith('.html')).sort().reverse();

    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f !== 'index.html')
      .sort()
      .reverse();

    res.render('history', { reports: htmlFiles });
  });
});

// GET / ：リクエスト（トップページ）へのルート定義
// app.get('/', (req, res) => {
//   // HTMLを返す処理
//   res.send(`
//     <h1>最新ニュースレポート</h1>
//     <p><a href="/public/news_report.pdf" target="_blank">PDFを表示</a></p>
//   `); // target="_blank" → 別タブでPDFを開く
// });

// ポート3000でサーバーを起動し、起動確認メッセージを出力
app.listen(3000, () => {
  console.log('✅ サーバー起動： http://localhost:3000');
});
