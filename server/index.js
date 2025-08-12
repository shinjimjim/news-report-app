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
app.use('/reports', express.static(path.join(__dirname, '../public/reports')));

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
// 「キーワードでタイトルを部分一致検索」しつつ、scope=recent5 の時だけ「直近5日分に限定」→ 同じ日付（＝レポートファイル）単位でグルーピングしてJSONを返します。
app.get('/search', async (req, res) => {
  // クエリ取得
  const q = (req.query.q || '').trim(); // GET /search?q=... を受け取るAPI。trim() で前後空白を除去。q はタイトル検索用キーワード。空なら即終了（無駄なDBアクセスを回避）。
  const scope = (req.query.scope || '').trim(); // scope は絞り込みオプション。recent5 指定時だけ検索対象日付を「最後の5日」に限定。
  if (!q) return res.json([]);

  // DB接続と結果入れ物
  const conn = await mysql.createConnection(dbConfig);
  let rows = [];

  // scope=recent5 のロジック
  if (scope === 'recent5') { // レポート単位＝日付ごとの最新5日 を取得。
    const [dateRows] = await conn.execute(
      `SELECT date AS dt
         FROM headlines
        GROUP BY date
        ORDER BY date DESC
        LIMIT 5`
    );
    const dates = dateRows.map(r => r.dt);
    if (dates.length === 0) {
      await conn.end();
      return res.json([]);
    }

    // その5日分に限定して検索
    const placeholders = dates.map(() => '?').join(','); // 取得した 5つの日付だけ を IN (?, ?, ?, ?, ?) で絞り込み、さらにタイトルLIKEで検索。
    const params = [`%${q}%`, ...dates];

    const [r] = await conn.execute(
      `SELECT DATE_FORMAT(date,'%Y-%m-%d') AS ymd, id, title, url
         FROM headlines
        WHERE title LIKE ?
          AND date IN (${placeholders})
        ORDER BY date DESC`,
      params
    );
    rows = r;
  } else {
    // 従来の全期間検索
    const [r] = await conn.execute(
      `SELECT DATE_FORMAT(date,'%Y-%m-%d') AS ymd, id, title, url
         FROM headlines
        WHERE title LIKE ?
        ORDER BY date DESC
        LIMIT 300`,
      [`%${q}%`]
    );
    rows = r;
  }

  await conn.end();

  // レポート（=日付）ごとにグルーピング
  const map = new Map();
  for (const r of rows) {
    const filename = `news_${r.ymd}.html`; // ymd（例：2025-08-01）から レポートHTMLのファイル名 を組み立て、Map で束ねる。
    if (!map.has(filename)) {
      map.set(filename, {
        filename,
        displayName: formatReportName(filename),
        items: []
      });
    }
    map.get(filename).items.push({
      id: r.id,
      title: r.title,
      url: r.url
    });
  }
  res.json([...map.values()]);
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

// 検索結果ページ
app.get('/search-page', async (req, res) => { // async 関数なので、中で await が使える。
  // クエリパラメータの取得と整形
  const keyword = (req.query.q || '').trim(); //URLの ?q=... 部分からキーワードを取得。.trim() で前後の空白を削除。|| '' で未指定時は空文字にする。
  const scope   = (req.query.scope || '').trim();
  // キーワードがない場合の処理
  if (!keyword) return res.render('search_results', { keyword, results: [], scope });

  // MySQLに接続
  const conn = await mysql.createConnection(dbConfig); // mysql.createConnection() で単発のDB接続を作成。await で接続完了を待ってから次へ進む。
  let rows = [];

  if (scope === 'recent5') {
    // 直近5日（＝5レポート分）の日付を取得
    const [dateRows] = await conn.execute(
      `SELECT date AS dt FROM headlines GROUP BY date ORDER BY date DESC LIMIT 5`
    );
    const dates = dateRows.map(r => r.dt);
    if (dates.length === 0) {
      await conn.end();
      return res.render('search_results', { keyword, results: [], scope });
    }

    // その5日分に限定して検索
    const placeholders = dates.map(() => '?').join(',');
    const params = [`%${keyword}%`, ...dates];
    const [r] = await conn.execute(
      `SELECT id, date, title, url
         FROM headlines
        WHERE title LIKE ?
          AND date IN (${placeholders})
        ORDER BY date DESC`,
      params
    );
    rows = r;
  } else {
    // 全期間
    const [r] = await conn.execute(
      `SELECT id, date, title, url
         FROM headlines
        WHERE title LIKE ?
        ORDER BY date DESC`,
      [`%${keyword}%`]
    );
    rows = r;
  }

  await conn.end();
  res.render('search_results', { keyword, results: rows, scope });
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
