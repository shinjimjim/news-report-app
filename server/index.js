const express = require('express'); // expressモジュールを読み込む。Node.jsでWebサーバーを簡単に作れる
const path = require('path'); // パス操作用モジュールを読み込む。OSに依存しないファイルパスの操作ができます。
const fs = require('fs'); // ファイル・ディレクトリ操作用（Node.js標準）
const cheerio = require('cheerio');

const app = express(); // Expressアプリケーション（サーバー）を作成

app.set('view engine', 'ejs'); // ejsをテンプレートエンジンとして使用
app.set('views', path.join(__dirname, 'views')); // テンプレートのディレクトリ

// /public パスで静的ファイルを公開する設定
app.use('/public', express.static(path.join(__dirname, '../public'))); // express.static() は指定フォルダ内のファイル（PDFや画像など）をそのまま公開できるようにします。path.join(__dirname, '../public') は public フォルダまでの絶対パスを作っています。__dirname は現在のファイルのあるディレクトリ。その1つ上の ../public フォルダを指します。

// ファイル名 → 日本語表示
function formatReportName(filename) {
  const match = filename.match(/^news_(\d{4})-(\d{2})-(\d{2})\.html$/);
  if (match) {
    const [_, year, month, day] = match;
    return `${year}年${parseInt(month)}月${parseInt(day)}日版`;
  }
  return filename;
}

// GET / ：リクエスト（トップページ）へのルート定義（最新HTML＋履歴5件）
app.get('/', (req, res) => {
  const historyDir = path.join(__dirname, '../public/history');
  //履歴フォルダの中から最新のHTMLレポートを抽出し、最大5件を整形して返す
  fs.readdir(historyDir, (err, files) => { //fs.readdir()はNode.js標準のファイルシステム操作関数。第一引数 historyDir に指定されたディレクトリの中身（ファイル名の配列）を取得します。第二引数は コールバック関数、err : 読み込みエラーがあれば入る（例：フォルダがない、権限がない）、files: 読み込んだファイル名の配列（["news_2025-08-01.html", "news_2025-07-31.html", ...]）
    if (err) return res.status(500).send('履歴フォルダの読み込みに失敗しました'); //フォルダが存在しない場合や権限エラーなどで読み込みが失敗したとき、HTTPレスポンスとして 500（サーバーエラー） を返します。return を使うことで、この時点で処理を終了します。

    // HTMLファイルのみ取得して新しい順にソート（index.htmlは除外）
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f !== 'index.html') // HTMLのみ、index.html除外
      .sort() // ファイル名昇順
      .reverse(); // 新しい順に
    // 最新HTMLは配列の先頭
    const latestHtmlFile = htmlFiles.length > 0 ? htmlFiles[0] : null;
    // 履歴は最大5件
    const recentReports = htmlFiles.slice(0, 5)
      .map(file => ({ //.map() で配列の中身を新しい形に変換します。file という文字列を { filename, displayName } というオブジェクトに変換。
      filename: file, //filename : 実際のファイル名
      displayName: formatReportName(file) //displayName : formatReportName(file) の戻り値
    }));

    res.render('index', { latestHtmlFile, recentReports, formatReportName }); // index.ejsに変数を渡す
  });
});

// 履歴ページ（全履歴表示）
app.get('/history', (req, res) => {
  const historyDir = path.join(__dirname, '../public/history');

  fs.readdir(historyDir, (err, files) => {
    if (err) return res.status(500).send('履歴フォルダの読み込みに失敗しました');

    // HTMLファイルのみ取得して新しい順にソート（index.htmlは除外）
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f !== 'index.html')
      .sort()
      .reverse()
      .map(file => ({
        filename: file,
        displayName: formatReportName(file)
      }));

    res.render('history', { reports: htmlFiles }); // history.ejs に渡す
  });
});

// ニュース本文キーワード検索API
app.get('/search', (req, res) => {
  const keyword = (req.query.q || '').toLowerCase();
  if (!keyword) return res.json([]);

  const historyDir = path.join(__dirname, '../public/history');
  const results = [];

  fs.readdirSync(historyDir)
    .filter(f => f.endsWith('.html') && f !== 'index.html')
    .forEach(file => {
      const filePath = path.join(historyDir, file);
      const html = fs.readFileSync(filePath, 'utf8');
      const $ = cheerio.load(html);

      // 見出し・本文テキストを結合
      const textContent = $('h1,h2,h3,p,li').text().toLowerCase();
      if (textContent.includes(keyword)) {
        results.push({
          filename: file,
          displayName: formatReportName(file)
        });
      }
    });

  res.json(results);
});

// ポート3000でサーバーを起動し、起動確認メッセージを出力
app.listen(3000, () => {
  console.log('✅ サーバー起動： http://localhost:3000');
});
