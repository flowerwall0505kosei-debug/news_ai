# AI ITニュース

ITmediaのRSSからITニュースを取得し、OpenAI APIで重要ニュースの選定、要約、重要度判定、カテゴリ分類を行い、GitHub Pagesで公開できる静的HTMLを生成するアプリです。

## 処理の流れ

```txt
ITmedia RSS
↓
agent.py でニュース取得
↓
OpenAI APIで選定・要約・重要度判定・カテゴリ分類
↓
data/news.json に保存
↓
generate_site.py で docs/index.html を生成
↓
GitHub Pagesで docs/index.html を公開
```

## ファイル構成

```txt
news_ai/
├─ agent.py             # GitHub Pages用。RSS取得、AI要約、JSON保存
├─ agent_mysql.py       # 旧MySQL保存版の控え
├─ app.py               # 旧Flask + MySQL版のローカル確認用
├─ generate_site.py     # data/news.json から静的HTMLを生成
├─ requirements.txt     # 必要ライブラリ
├─ README.md
├─ .gitignore
├─ .env.example
├─ data/
│  └─ news.json
└─ docs/
   ├─ index.html
   └─ style.css
```

## ローカルでの実行方法

1. 必要ライブラリをインストールします。

```bash
pip install -r requirements.txt
```

2. `.env.example` を参考に、同じフォルダに `.env` を作成します。

```env
OPENAI_API_KEY=自分のAPIキー
OPENAI_MODEL=gpt-5-mini
```

3. ニュース取得とAI要約を実行します。

```bash
python agent.py
```

4. 静的サイトを生成します。

```bash
python generate_site.py
```

実行後、`data/news.json` と `docs/index.html` が更新されます。ブラウザで `docs/index.html` を開くと結果を確認できます。

## .env の設定

OpenAI APIキーはコード、HTML、JavaScriptに直接書かないでください。必ず `.env` または環境変数で指定します。

```env
OPENAI_API_KEY=自分のAPIキー
```

`.env` は `.gitignore` に入っているため、GitHubにはアップロードしません。

旧MySQL版を使う場合だけ、必要に応じて次も設定します。

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=自分のMySQLパスワード
MYSQL_DATABASE=news_ai
```

## GitHub Pagesでの公開方法

1. `python agent.py` を実行して `data/news.json` を更新します。
2. `python generate_site.py` を実行して `docs/index.html` を生成します。
3. GitHubにリポジトリをpushします。
4. GitHubのリポジトリ画面で `Settings` → `Pages` を開きます。
5. `Build and deployment` のSourceで `Deploy from a branch` を選びます。
6. Branchを `main`、フォルダを `/docs` に設定して保存します。

GitHub PagesではFlaskやMySQLは動かさず、`docs/index.html` と `docs/style.css` を公開します。

## 今後の改善案

- GitHub Actionsで毎朝自動更新する
- `data/news.json` の件数が増えたら古いニュースを自動整理する
- カテゴリ別フィルタや重要度フィルタを追加する
- RSS取得元を複数に増やす
- エラー発生時のログを分かりやすくする
