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

## GitHub Actionsでの自動更新

`.github/workflows/update-news.yml` に、毎朝7時17分ごろ（日本時間）にニュースを自動更新するワークフローを用意しています。

使う前に、GitHubのリポジトリ画面でOpenAI APIキーをSecretに登録してください。

1. GitHubでリポジトリを開きます。
2. `Settings` → `Secrets and variables` → `Actions` を開きます。
3. `New repository secret` をクリックします。
4. `Name` に `OPENAI_API_KEY` と入力します。
5. `Secret` にOpenAI APIキーを入力して保存します。

設定後は、毎朝自動で次の処理が実行されます。

```txt
python agent.py
↓
python generate_site.py
↓
data/news.json と docs/index.html に変更があれば自動commit/push
↓
GitHub Pagesに反映
```

すぐに試したい場合は、GitHubの `Actions` タブから `Update news site` を選び、`Run workflow` を押すと手動実行できます。

## 今後の改善案

- `data/news.json` の件数が増えたら古いニュースを自動整理する
- カテゴリ別フィルタや重要度フィルタを追加する
- RSS取得元を複数に増やす
- エラー発生時のログを分かりやすくする
