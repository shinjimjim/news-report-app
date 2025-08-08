const express = require('express'); // expressモジュールを読み込む。Node.jsでWebサーバーを簡単に作れる
const path = require('path'); // パス操作用モジュールを読み込む。OSに依存しないファイルパスの操作ができます。
const fs = require('fs'); // ファイル・ディレクトリ操作用（Node.js標準）
const cheerio = require('cheerio'); // cheerio: HTMLをDOMのように扱えるjQuery風API（本文検索用）
const app = express(); // Expressアプリケーション（サーバー）を作成

require('dotenv').config({ path: path.join(__dirname, '../.env') }); //dotenv: .env から DB接続情報 を読み込む（秘匿）

// ejsをテンプレートエンジンとして使用
app.set('view engine', 'ejs'); // EJS: res.render('index', data) → views/index.ejs を描画
// テンプレートのディレクトリ
app.set('views', path.join(__dirname, 'views'));
// /public パスで静的ファイルを公開する設定
app.use('/public', express.static(path.join(__dirname, '../public'))); // express.static() は指定フォルダ内のファイル（PDFや画像など）をそのまま公開できるようにします。path.join(__dirname, '../public') は public フォルダまでの絶対パスを作っています。__dirname は現在のファイルのあるディレクトリ。その1つ上の ../public フォルダを指します。

// ファイル名 → 日本語表示
function formatReportName(filename) {
  const match = filename.match(/^news_(\d{4})-(\d{2})-(\d{2})\.html$/);
  if (match) {
    const [_, year, month, day] = match;
    return `${year}年${parseInt(month)}月${parseInt(day)}日版`; // 例: news_2025-08-01.html → 2025年8月1日版
  }
  return filename;
}

// カテゴリ定義（画面ボタンなどに使う）
const CATEGORIES = [
  "政治", "経済", "ビジネス", "金融・マネー", "国際", "気象・災害", "地域・地方", "暮らし",
  "医療・健康", "教育・受験", "社会", "交通・事故", "スポーツ", "エンタメ",
  "科学・文化", "テクノロジー", "IT・インターネット", "AI・生成AI", "セキュリティ・犯罪", "労働・雇用", "食・グルメ", "ペット・動物", "旅行・観光", "その他"
];

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

    res.render('index', {
      pageTitle: 'トップ',
      latestHtmlFile,
      recentReports,
      formatReportName,
      categories: CATEGORIES
    }); //// index.ejs に渡す
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
  // クエリパラメータの取得
  const keyword = (req.query.q || '').toLowerCase(); //URLの ?q=... 部分から検索ワードを取得。|| '' で未指定時に空文字にする（undefined対策）.toLowerCase() で小文字化 → 検索時に大文字・小文字を区別しないため。
  // キーワード未指定なら空配列を返す
  if (!keyword) return res.json([]); //検索ワードが空なら何も検索せず、即終了。res.json([]) は空配列をJSONで返す（HTTP 200）。

  // 履歴ディレクトリのパス作成
  const historyDir = path.join(__dirname, '../public/history'); //現在のファイルがあるディレクトリ（__dirname）からの相対パスで../public/history フォルダを指す絶対パスを作成。
  // 検索結果を入れる配列用意
  const results = []; // 条件一致したHTMLファイルの情報（ファイル名・表示名）を格納します。

  // ディレクトリ内のHTMLファイルを全件取得
  fs.readdirSync(historyDir) // fs.readdirSync() → 同期処理で historyDir 内のファイル一覧を取得。
    .filter(f => f.endsWith('.html') && f !== 'index.html') // .filter(...) で以下の条件に一致するファイルだけ残す:.endsWith('.html') → HTMLファイルのみ。f !== 'index.html' → 一覧ページ用のindex.htmlは除外
    // 各HTMLファイルを読み込み＆検索
    .forEach(file => { // filePath → ファイルの絶対パス作成。
      const filePath = path.join(historyDir, file);
      const html = fs.readFileSync(filePath, 'utf8'); // fs.readFileSync(..., 'utf8') → HTMLファイルを文字コードUTF-8で読み込み。
      const $ = cheerio.load(html); // cheerio.load(html) → HTML文字列をDOM風オブジェクトとして扱えるようにする。jQueryと同じように $('タグ') で要素を取得可能。

      // 見出し・本文テキストを結合
      const textContent = $('h1,h2,h3,p,li').text().toLowerCase(); // $('h1,h2,h3,p,li') → HTML内の全h1,h2,h3,p,liタグを選択。.text() → 選択要素のテキスト部分だけを連結して取得（タグは除外）。.toLowerCase() → 検索のために小文字化。
      // キーワード含有チェック
      if (textContent.includes(keyword)) { // .includes(keyword) → 単純部分一致でキーワードがあるか確認。
        results.push({ // 一致したら results にオブジェクトを追加
          filename: file, // filename → 実際のファイル名（例: "news_2025-08-01.html")
          displayName: formatReportName(file) // displayName → formatReportName(file)で変換（例: "2025年8月1日版"）
        });
      }
    });

  res.json(results);
});

// MySQLから記事タイトルをキーワード検索して、HTMLページとして返す機能
// MySQL接続設定
const mysql = require('mysql2/promise'); // mysql2/promise を使って async/await で書ける
// 接続情報を .env から取得
const dbConfig = {
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  database: process.env.DB_NAME
};

// 検索結果ページ（SEO & 広告向け）
app.get('/search-page', async (req, res) => { // async 関数なので、中で await が使える。
  // クエリパラメータの取得と整形
  const keyword = (req.query.q || '').trim(); //URLの ?q=... 部分からキーワードを取得。.trim() で前後の空白を削除。|| '' で未指定時は空文字にする。
  // キーワードがない場合の処理
  if (!keyword) {
    return res.render('search_results', { keyword, results: [] }); // 空文字なら検索せず、空の結果をsearch_results.ejsに渡して終了。return を使って処理を中断するのがポイント。
  }

  // MySQLに接続
  const conn = await mysql.createConnection(dbConfig); // mysql.createConnection() で単発のDB接続を作成。await で接続完了を待ってから次へ進む。
  // 検索クエリの実行
  const [rows] = await conn.execute( // conn.execute() → プレースホルダ付きSQLを実行。
    `SELECT id, date, title, url
     FROM headlines
     WHERE title LIKE ?
     ORDER BY date DESC`,
    [`%${keyword}%`]
  ); // ? に [%${keyword}%] が安全に埋め込まれる（SQLインジェクション対策）。LIKE 検索なので部分一致。ORDER BY date DESC → 新しい日付から順に並び替え。戻り値構造:rows: 検索結果（配列）fields: カラム情報（今回は使わない）
  // 接続終了
  conn.end();

  // 検索結果をHTMLとして返す
  res.render('search_results', { keyword, results: rows }); // views/search_results.ejs を描画。EJS側でループしてタイトルや日付、URLを表示する。
});

// カテゴリ別フィルター表示ルート
app.get('/category/:name', async (req, res) => { // :name は URLパラメータ で、/category/政治 や /category/経済 のように使える。
  // URLのカテゴリ名を取得
  const category = decodeURIComponent(req.params.name); // req.params.name → URLパス中の:name部分の文字列を取得。decodeURIComponent() は、URLエンコードされた日本語を元に戻すために必要。

  try {
    // DB接続開始
    const connection = await mysql.createConnection(dbConfig); // ここでは単発接続（createConnection）高トラフィック時は接続プール（mysql.createPool）推奨。
    // カテゴリ別の記事を取得
    const [rows] = await connection.execute(
      'SELECT title, url, date FROM headlines WHERE category = ? ORDER BY date DESC',
      [category]
    ); // [category] はSQLの ? に安全に埋め込まれる（SQLインジェクション防止）
    // 接続終了
    await connection.end(); // await を付けて確実に終了を待つ。

    // HTMLページを描画
    res.render('category', { // views/category.ejs を描画。
      pageTitle: `${category} のニュース一覧`, // pageTitle: ページタイトル用（ブラウザタブなど）
      category, // category: 現在表示中のカテゴリ名
      headlines: rows // headlines: DBから取得した記事リスト（EJSでループ表示）
    });

    // エラーハンドリング
  } catch (err) {
    console.error(err);
    res.status(500).send('サーバーエラー'); // DB接続エラーやクエリ失敗時にログ出力して500エラーを返す。
  }
});

// ポート3000でサーバーを起動し、起動確認メッセージを出力
app.listen(3000, () => {
  console.log('✅ サーバー起動： http://localhost:3000');
});
