# Tech Compass 505

Tech Compass 505 は、ITmedia RSSからITニュースを取得し、OpenAI APIで重要ニュースの選定、要約、重要度判定、カテゴリ分類を行い、GitHub Pagesで公開できる静的HTMLサイトを生成するアプリケーションです。

## 処理の流れ

```txt
ITmedia RSS
-> agent.py でニュース候補を取得
-> OpenAI APIで重要ニュースを選定・要約・分類
-> data/news.json に保存
-> generate_site.py で docs/ 配下の静的サイトを生成
-> GitHub Pagesで docs/ を公開
```

## 主な機能

- ITmedia RSSからニュース候補を取得
- JST基準で昨日の記事を優先取得
- 昨日の記事がRSS内にない場合は最新10件を候補化
- OpenAI APIによるニュース選定、要約、重要度判定、カテゴリ分類
- `data/news.json` への蓄積
- 重要度に応じた古いニュースの自動整理
- GitHub Pages向けの静的サイト生成
- キーワード、カテゴリ、重要度、日付によるブラウザ内検索

## ファイル構成

```txt
techcompass/
├─ agent.py                 # RSS取得、AI選定、data/news.json保存
├─ generate_site.py         # data/news.jsonからdocs/の静的サイトを生成
├─ agent_mysql.py           # 旧MySQL保存方式のエージェント
├─ app.py                   # MySQL版のローカル確認用Flaskアプリ
├─ requirements.txt         # Python依存ライブラリ
├─ run_agent.bat            # Windows向け更新バッチ
├─ data/
│  └─ news.json             # ニュース蓄積データ
├─ docs/
│  ├─ index.html            # トップページ
│  ├─ news/index.html       # ニュース一覧
│  ├─ ai/index.html         # AIニュース
│  ├─ search/index.html     # 検索ページ
│  ├─ news.json             # 公開・検索用JSON
│  ├─ search.js             # 検索処理
│  └─ style.css             # サイト共通CSS
├─ specification/
│  ├─ README.md             # 設計書索引
│  ├─ system-design.md      # システム設計
│  ├─ data-design.md        # データ設計
│  └─ operation-design.md   # 運用設計
└─ .github/workflows/
   └─ update-news.yml       # 自動更新ワークフロー
```

## セットアップ

依存ライブラリをインストールします。

```bash
pip install -r requirements.txt
```

`.env.example` を参考に、同じフォルダに `.env` を作成します。

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5-mini
```

MySQL版を使う場合だけ、次の値も設定します。

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=news_ai
```

## ローカル実行

ニュース取得とAI選定を実行します。

```bash
python agent.py
```

静的サイトを生成します。

```bash
python generate_site.py
```

実行後、`data/news.json` と `docs/` 配下のHTML・JSONが更新されます。ブラウザで `docs/index.html` を開くと確認できます。

検索ページをHTTPサーバー経由で確認したい場合は、次のように起動します。

```bash
python -m http.server 8000 -d docs
```

## サイト構成

- トップページ: 昨日のニュースと直近の重要ニュースを表示
- ニュース一覧: 保存中の全ニュースを新しい順に表示
- AIニュース: カテゴリが `AI` のニュースだけを表示
- 検索ページ: キーワード、カテゴリ、重要度、日付で絞り込み

各ニュースカードには、カテゴリ、公開日時、重要度、タイトル、要約、選定理由、記事リンク、保存日時を表示します。

## ニュースの保持期間

`agent.py` は重要度に応じて、保存期間を過ぎたニュースを `data/news.json` から整理します。

| 重要度 | 保持期間 |
| --- | --- |
| 1 | 7日 |
| 2 | 7日 |
| 3 | 30日 |
| 4 | 183日 |
| 5 | 無期限 |

## GitHub Pagesでの公開

GitHub PagesではFlaskやMySQLは動かさず、`docs/` 配下の静的ファイルを公開します。

設定例:

1. GitHubのリポジトリで `Settings` を開く。
2. `Pages` を開く。
3. Sourceで `Deploy from a branch` を選ぶ。
4. Branchを `main`、Folderを `/docs` に設定する。

## GitHub Actionsでの自動更新

`.github/workflows/update-news.yml` に、毎日 03:16 JST にニュースサイトを更新するワークフローがあります。

GitHub Actionsを使う前に、Repository Secretsに次を登録してください。

```txt
OPENAI_API_KEY
```

ワークフローは次の処理を行います。

```txt
python agent.py
-> python generate_site.py
-> data/news.json と docs/ に変更があれば自動commit/push
-> GitHub Pagesに反映
```

手動で試す場合は、GitHubの `Actions` タブから `Update news site` を選び、`Run workflow` を実行します。

## 設計書

設計情報は [specification/README.md](specification/README.md) から参照できます。

- [システム設計書](specification/system-design.md)
- [データ設計書](specification/data-design.md)
- [運用設計書](specification/operation-design.md)

## 注意事項

- `.env` はGit管理に含めないでください。
- OpenAI APIキーをHTML、JavaScript、JSONに直接書かないでください。
- 現行の公開経路は `agent.py`、`generate_site.py`、`data/news.json`、`docs/` です。
- `app.py` と `agent_mysql.py` は旧MySQL方式またはローカル確認用です。
